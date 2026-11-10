"""Report placeholder resolution and final rendering per Task 4.2."""

import re
from typing import Any

from athena.schemas import Report, ToolResult, VerificationSummary


def resolve_placeholders(
    report: Report,
    tool_results: list[ToolResult],
    decimal_places: int = 2,
) -> Report:
    """Replace {{tool_id.metric}} placeholders in report text with actual formatted values."""
    rep = report.model_copy(deep=True)

    metrics_map: dict[tuple[str, str], float | int | str] = {}
    for tr in tool_results:
        for m in tr.metrics:
            metrics_map[(tr.id, m.name)] = m.value

    def _replace_match(match: re.Match[str]) -> str:
        ph = match.group(1).strip()
        parts = ph.split(".", 1)
        if len(parts) == 2:
            tid, mname = parts[0], parts[1]
            if (tid, mname) in metrics_map:
                val = metrics_map[(tid, mname)]
                if isinstance(val, float):
                    return f"{val:.{decimal_places}f}"
                return str(val)
        return match.group(0)

    # 1. Resolve in TLDR
    rep.tldr = re.sub(r"\{\{([^}]+)\}\}", _replace_match, rep.tldr)

    # 2. Resolve in Findings
    for finding in rep.findings:
        finding.text = re.sub(r"\{\{([^}]+)\}\}", _replace_match, finding.text)

    # 3. Resolve in Recommendations
    for rec in rep.recommendations:
        rec.text = re.sub(r"\{\{([^}]+)\}\}", _replace_match, rec.text)

    # 4. Resolve in Caveats
    rep.caveats = [re.sub(r"\{\{([^}]+)\}\}", _replace_match, c) for c in rep.caveats]

    return rep


def format_report(report: Report) -> dict[str, Any]:
    """Produce dictionary payload suitable for UI and API consumption."""
    return report.model_dump()


def render_markdown(
    report: Report,
    verification: VerificationSummary | None = None,
) -> str:
    """Format report into clean, professional GitHub-flavored markdown."""
    lines = [
        f"# Analytical Report: {report.question}\n",
        f"**Answerable:** {'Yes' if report.answerable else 'No'}\n",
        "## Executive Summary",
        f"{report.tldr}\n",
    ]

    if report.findings:
        lines.append("## Key Findings")
        for f in report.findings:
            ev_str = ", ".join(f"{e.tool_result_id}.{e.metric}" for e in f.evidence)
            prefix = f"- **[{f.id}]** ({f.claim_type.value}): "
            lines.append(f"{prefix}{f.text}")
            if ev_str:
                lines.append(f"  *Evidence:* `{ev_str}`")
        lines.append("")

    if report.recommendations:
        lines.append("## Recommendations")
        for idx, rec in enumerate(report.recommendations, 1):
            supported = f" (Supported by {', '.join(rec.supported_by)})" if rec.supported_by else ""
            lines.append(f"{idx}. [{rec.confidence.value.upper()}] {rec.text}{supported}")
        lines.append("")

    if report.caveats:
        lines.append("## Caveats & Limitations")
        for c in report.caveats:
            lines.append(f"- {c}")
        lines.append("")

    if verification:
        status_color = "🟢 PASS" if verification.failed == 0 else "🟠 ATTENTION"
        lines.extend(
            [
                "## Verification Summary",
                (
                    f"**Status:** {status_color} "
                    f"({verification.passed}/{verification.total_checks} checks passed)"
                ),
            ]
        )
        if verification.unverified_claims > 0:
            lines.append(f"- Unverified claims: {verification.unverified_claims}")
        if verification.repairs_attempted > 0:
            lines.append(f"- Automated repair iterations: {verification.repairs_attempted}")

    return "\n".join(lines)
