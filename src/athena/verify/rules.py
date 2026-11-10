"""Deterministic verifier rules V1 through V5 per Task 4.1."""

import re
from typing import Any

from athena.config import Settings
from athena.config import settings as global_settings
from athena.schemas import ClaimType, Report, ToolResult, VerificationResult

ALLOWED_LITERALS = {
    0.0,
    1.0,
    2.0,
    3.0,
    4.0,
    5.0,
    10.0,
    20.0,
    50.0,
    100.0,
    0.05,
    0.01,
    0.001,
}

CAUSAL_KEYWORDS = [
    r"\bcauses\b",
    r"\bcaused by\b",
    r"\bleads to\b",
    r"\bresults in\b",
    r"\bdue to\b",
    r"\bbecause of\b",
    r"\beffect of\b",
]


def check_v1_numeric_grounding(
    report: Report,
    tool_results: list[ToolResult],
    app_settings: Settings | None = None,
) -> list[VerificationResult]:
    """Verify numeric claims: resolve {{...}} placeholders and verify literal numbers."""
    cfg = app_settings or global_settings
    results: list[VerificationResult] = []

    metrics_map: dict[tuple[str, str], float | int | str] = {}
    for tr in tool_results:
        for m in tr.metrics:
            metrics_map[(tr.id, m.name)] = m.value

    if not report.findings:
        return [VerificationResult(rule="V1", passed=True)]

    for finding in report.findings:
        text = finding.text
        finding_passed = True

        placeholders = re.findall(r"\{\{([^}]+)\}\}", text)
        for ph in placeholders:
            parts = ph.strip().split(".", 1)
            if len(parts) == 2:
                tid, mname = parts[0], parts[1]
                if (tid, mname) not in metrics_map:
                    finding_passed = False
                    results.append(
                        VerificationResult(
                            rule="V1",
                            finding_id=finding.id,
                            passed=False,
                            issue=f"Placeholder '{{{{{ph}}}}}' not found in cited tool results.",
                            suggestion=f"Verify tool ID '{tid}' and metric name '{mname}'.",
                        )
                    )
            else:
                finding_passed = False
                results.append(
                    VerificationResult(
                        rule="V1",
                        finding_id=finding.id,
                        passed=False,
                        issue=f"Malformed placeholder syntax: '{{{{{ph}}}}}'.",
                        suggestion="Use format {{tool_id.metric_name}}.",
                    )
                )

        cleaned_text = re.sub(r"\{\{[^}]+\}\}", "", text)
        cleaned_text = re.sub(r"\b[fF]\d+\b", "", cleaned_text)

        raw_numbers = re.findall(r"\b(?<!\w)(\d+(?:\.\d+)?%?)(?!\w)", cleaned_text)
        evidence_metrics = []
        for ev in finding.evidence:
            val = metrics_map.get((ev.tool_result_id, ev.metric))
            if val is not None and isinstance(val, (int, float)):
                evidence_metrics.append(float(val))

        for num_str in raw_numbers:
            is_pct = num_str.endswith("%")
            val_str = num_str[:-1] if is_pct else num_str
            try:
                num_val = float(val_str)
            except ValueError:
                continue

            if num_val in ALLOWED_LITERALS:
                continue

            matched = False
            for m_val in evidence_metrics:
                tol = max(
                    cfg.numeric_tolerance_absolute,
                    cfg.numeric_tolerance_relative * abs(m_val),
                )
                if abs(num_val - m_val) <= tol or (is_pct and abs(num_val / 100.0 - m_val) <= tol):
                    matched = True
                    break

            if not matched and not evidence_metrics and num_val not in ALLOWED_LITERALS:
                finding_passed = False
                results.append(
                    VerificationResult(
                        rule="V1",
                        finding_id=finding.id,
                        passed=False,
                        issue=f"Literal number {num_str} not grounded in cited evidence.",
                        suggestion="Ground number using placeholder syntax {{tool_id.metric}}.",
                    )
                )

        if finding_passed:
            results.append(VerificationResult(rule="V1", finding_id=finding.id, passed=True))

    return results


def check_v2_claim_evidence_consistency(
    report: Report,
    tool_results: list[ToolResult],
    app_settings: Settings | None = None,
) -> list[VerificationResult]:
    """Verify consistency between claims (significance, direction, strength) and evidence."""
    cfg = app_settings or global_settings
    results: list[VerificationResult] = []

    metrics_map: dict[tuple[str, str], Any] = {}
    for tr in tool_results:
        for m in tr.metrics:
            metrics_map[(tr.id, m.name)] = m.value

    if not report.findings:
        return [VerificationResult(rule="V2", passed=True)]

    for finding in report.findings:
        text_lower = finding.text.lower()
        finding_passed = True

        if "statistically significant" in text_lower or "significant difference" in text_lower:
            p_values = []
            for ev in finding.evidence:
                val = metrics_map.get((ev.tool_result_id, ev.metric))
                if ev.metric in ("p_value", "p_val", "p_value_corrected") and isinstance(
                    val, (int, float)
                ):
                    p_values.append(float(val))

            if p_values and any(p >= cfg.alpha for p in p_values):
                finding_passed = False
                results.append(
                    VerificationResult(
                        rule="V2",
                        finding_id=finding.id,
                        passed=False,
                        issue="Claim asserts significance but cited p-value >= alpha.",
                        suggestion="State that no significant difference was detected.",
                    )
                )

        pos_words = ["higher", "greater", "increase", "increased", "positive correlation"]
        neg_words = ["lower", "smaller", "decrease", "decreased", "negative correlation"]

        effects = []
        for ev in finding.evidence:
            val = metrics_map.get((ev.tool_result_id, ev.metric))
            if isinstance(val, (int, float)) and ev.metric in (
                "pearson_r",
                "spearman_rho",
                "cohen_d",
                "mean_diff",
                "slope",
            ):
                effects.append(float(val))

        if any(w in text_lower for w in pos_words) and effects:
            if all(e < 0 for e in effects):
                finding_passed = False
                results.append(
                    VerificationResult(
                        rule="V2",
                        finding_id=finding.id,
                        passed=False,
                        issue="Claim asserts positive direction, but cited effect is negative.",
                        suggestion="Correct claimed direction to match negative effect size.",
                    )
                )

        if any(w in text_lower for w in neg_words) and effects:
            if all(e > 0 for e in effects):
                finding_passed = False
                results.append(
                    VerificationResult(
                        rule="V2",
                        finding_id=finding.id,
                        passed=False,
                        issue="Claim asserts negative direction, but cited effect is positive.",
                        suggestion="Correct claimed direction to match positive effect size.",
                    )
                )

        if "strong correlation" in text_lower:
            r_vals = [
                float(metrics_map.get((ev.tool_result_id, ev.metric), 0))
                for ev in finding.evidence
                if ev.metric in ("pearson_r", "spearman_rho")
            ]
            if r_vals and any(abs(r) < 0.7 for r in r_vals):
                finding_passed = False
                results.append(
                    VerificationResult(
                        rule="V2",
                        finding_id=finding.id,
                        passed=False,
                        issue="Claim asserts 'strong correlation', but |r| < 0.7.",
                        suggestion="Describe correlation as moderate or weak per thresholds.",
                    )
                )

        if finding.claim_type == ClaimType.predictive:
            perf_metrics = [
                ev.metric
                for ev in finding.evidence
                if ev.metric in ("roc_auc", "accuracy", "f1", "rmse", "mae", "r2")
            ]
            if not perf_metrics:
                finding_passed = False
                results.append(
                    VerificationResult(
                        rule="V2",
                        finding_id=finding.id,
                        passed=False,
                        issue="Predictive claim does not cite any model evaluation metrics.",
                        suggestion="Cite held-out evaluation metrics like accuracy, f1, or rmse.",
                    )
                )

        if finding_passed:
            results.append(VerificationResult(rule="V2", finding_id=finding.id, passed=True))

    return results


def check_v3_causal_language(report: Report) -> list[VerificationResult]:
    """Flag causal claims on observational data when claim_type is not causal."""
    results: list[VerificationResult] = []

    if not report.findings:
        return [VerificationResult(rule="V3", passed=True)]

    for finding in report.findings:
        matched_kw = None
        for pattern in CAUSAL_KEYWORDS:
            if re.search(pattern, finding.text, re.IGNORECASE):
                matched_kw = pattern.replace(r"\b", "")
                break

        if matched_kw and finding.claim_type != ClaimType.causal:
            results.append(
                VerificationResult(
                    rule="V3",
                    finding_id=finding.id,
                    passed=False,
                    issue=(
                        f"Finding uses causal language ('{matched_kw}') but claim_type "
                        f"is '{finding.claim_type}'. Observational data cannot establish causality."
                    ),
                    suggestion="Reframe finding as associational or correlational.",
                )
            )
        else:
            results.append(VerificationResult(rule="V3", finding_id=finding.id, passed=True))

    return results


def check_v4_linkage(
    report: Report,
    tool_results: list[ToolResult],
) -> list[VerificationResult]:
    """Verify evidence linkage across findings, recommendations, and execution trace."""
    results: list[VerificationResult] = []
    trace_ids = {tr.id for tr in tool_results if tr.id}
    finding_ids = {f.id for f in report.findings if f.id}

    for finding in report.findings:
        if not finding.evidence:
            results.append(
                VerificationResult(
                    rule="V4",
                    finding_id=finding.id,
                    passed=False,
                    issue=f"Finding '{finding.id}' has no cited evidence.",
                    suggestion="Attach tool evidence to support finding.",
                )
            )
        else:
            invalid_tools = [
                ev.tool_result_id for ev in finding.evidence if ev.tool_result_id not in trace_ids
            ]
            if invalid_tools:
                results.append(
                    VerificationResult(
                        rule="V4",
                        finding_id=finding.id,
                        passed=False,
                        issue=f"Finding '{finding.id}' cites unknown tool ID(s): {invalid_tools}.",
                        suggestion="Reference only tool result IDs that exist in the trace.",
                    )
                )
            else:
                results.append(VerificationResult(rule="V4", finding_id=finding.id, passed=True))

    for idx, rec in enumerate(report.recommendations):
        if not rec.supported_by:
            results.append(
                VerificationResult(
                    rule="V4",
                    passed=False,
                    issue=f"Recommendation #{idx + 1} has no supporting finding IDs.",
                    suggestion="Link recommendation to at least one valid finding ID.",
                )
            )
        else:
            unknown_findings = [fid for fid in rec.supported_by if fid not in finding_ids]
            if unknown_findings:
                results.append(
                    VerificationResult(
                        rule="V4",
                        passed=False,
                        issue=f"Rec #{idx + 1} cites unknown finding: {unknown_findings}.",
                        suggestion="Ensure supported_by contains valid finding IDs.",
                    )
                )

    if not results:
        results.append(VerificationResult(rule="V4", passed=True))

    return results


def check_v5_data_quality_propagation(
    report: Report,
    tool_results: list[ToolResult],
) -> list[VerificationResult]:
    """Verify that severe data quality issues propagate to caveats."""
    results: list[VerificationResult] = []
    caveats_lower = " ".join(report.caveats).lower()

    has_high_leakage = False
    for tr in tool_results:
        if tr.tool == "leakage_check" and tr.output:
            if tr.output.get("highest_severity") == "high":
                has_high_leakage = True
                break

    if has_high_leakage:
        if not any(k in caveats_lower for k in ("leakage", "leaky", "target leak")):
            results.append(
                VerificationResult(
                    rule="V5",
                    passed=False,
                    issue="High-severity target leakage detected, but caveats omit leakage.",
                    suggestion="Add a caveat stating performance metrics reflect leakage.",
                )
            )

    has_high_missing = False
    for tr in tool_results:
        if tr.tool == "profile_dataset" and tr.output:
            col_stats = tr.output.get("columns", {})
            for stats in col_stats.values():
                if isinstance(stats, dict) and stats.get("null_percent", 0) > 30.0:
                    has_high_missing = True
                    break

    if has_high_missing:
        if not any(k in caveats_lower for k in ("missing", "null", "missingness")):
            results.append(
                VerificationResult(
                    rule="V5",
                    passed=False,
                    issue="Columns have >30% missingness, but caveats omit missing data.",
                    suggestion="Add a caveat noting high column missingness.",
                )
            )

    if not results:
        results.append(VerificationResult(rule="V5", passed=True))

    return results
