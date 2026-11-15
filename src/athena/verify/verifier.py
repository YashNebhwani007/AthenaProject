"""Verifier coordinator and multi-turn repair loop per ADR-07 and Task 4.2."""

from athena.config import Settings
from athena.config import settings as global_settings
from athena.llm.base import LLMClient
from athena.logging import get_logger
from athena.schemas import Report, ToolResult, VerificationResult, VerificationSummary
from athena.verify.repair import build_repair_message, parse_repaired_report
from athena.verify.rules import (
    check_v1_numeric_grounding,
    check_v2_claim_evidence_consistency,
    check_v3_causal_language,
    check_v4_linkage,
    check_v5_data_quality_propagation,
)

logger = get_logger(__name__)


class Verifier:
    """Automated verification pipeline with LLM repair loop and graceful degradation."""

    def __init__(self, app_settings: Settings | None = None) -> None:
        self.settings = app_settings or global_settings

    def run_all_checks(
        self,
        report: Report,
        tool_results: list[ToolResult],
    ) -> list[VerificationResult]:
        """Execute all rules V1 through V5 against report and execution trace."""
        results: list[VerificationResult] = []
        results.extend(check_v1_numeric_grounding(report, tool_results, self.settings))
        results.extend(check_v2_claim_evidence_consistency(report, tool_results, self.settings))
        results.extend(check_v3_causal_language(report))
        results.extend(check_v4_linkage(report, tool_results))
        results.extend(check_v5_data_quality_propagation(report, tool_results))
        return results

    async def verify(
        self,
        report: Report,
        tool_results: list[ToolResult],
        llm_client: LLMClient | None = None,
    ) -> tuple[Report, VerificationSummary]:
        """Verify report, trigger repair loop on violations, degrade unfixable claims."""
        current_report = report.model_copy(deep=True)
        max_repairs = self.settings.max_repair_iterations
        repairs_attempted = 0

        while True:
            checks = self.run_all_checks(current_report, tool_results)
            failures = [c for c in checks if not c.passed]

            if not failures or repairs_attempted >= max_repairs or llm_client is None:
                break

            # Attempt repair
            repairs_attempted += 1
            repair_prompt = build_repair_message(failures)
            logger.info("verifier_repair_attempt", attempt=repairs_attempted, issues=len(failures))

            trace_summary_lines = []
            for tr in tool_results:
                m_info = ", ".join(f"{m.name}={m.value}" for m in tr.metrics[:8])
                trace_summary_lines.append(
                    f"- Tool ID '{tr.id}' ({tr.tool}): metrics=[{m_info or 'none'}]"
                )
            trace_summary = "\n".join(trace_summary_lines)

            try:
                repair_messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are Athena's Report Correction Engine. "
                            "Output ONLY valid Report JSON with the following structure:\n"
                            "{\n"
                            '  "question": "string",\n'
                            '  "answerable": true,\n'
                            '  "tldr": "string",\n'
                            '  "findings": [{"id": "f1", "text": "...", '
                            '"claim_type": "descriptive", "evidence": []}],\n'
                            '  "caveats": ["string"],\n'
                            '  "recommendations": [{"text": "...", "supported_by": ["f1"], '
                            '"confidence": "high"}]\n'
                            "}"
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Available executed tool evidence to cite:\n{trace_summary}\n\n"
                            "Previous report draft:\n"
                            f"{current_report.model_dump_json(indent=2)}\n\n"
                            f"{repair_prompt}"
                        ),
                    },
                ]
                resp = await llm_client.chat(messages=repair_messages, seed=self.settings.llm_seed)
                if resp.content:
                    current_report = parse_repaired_report(resp.content)
            except Exception as e:
                logger.warning("verifier_repair_failed", error=str(e))
                break

        # Final check execution
        final_checks = self.run_all_checks(current_report, tool_results)
        final_failures = [c for c in final_checks if not c.passed]
        passed_count = sum(1 for c in final_checks if c.passed)
        failed_count = len(final_failures)

        unverified_ids: list[str] = []
        if final_failures:
            # Graceful degradation: mark unverified findings
            failing_finding_ids = {f.finding_id for f in final_failures if f.finding_id}
            unverified_ids = sorted(list(failing_finding_ids))

            for finding in current_report.findings:
                if finding.id in failing_finding_ids:
                    if not finding.text.startswith("[UNVERIFIED]"):
                        finding.text = f"[UNVERIFIED] {finding.text}"

            for f in final_failures:
                msg = f"Unverified claim in {f.finding_id or 'report'}: {f.issue}"
                if msg not in current_report.caveats:
                    current_report.caveats.append(msg)

        summary = VerificationSummary(
            total_checks=len(final_checks),
            passed=passed_count,
            failed=failed_count,
            unverified_claims=len(unverified_ids),
            repairs_attempted=repairs_attempted,
            details=final_checks,
        )

        return current_report, summary
