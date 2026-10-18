"""Tests for report renderer and placeholder resolution per Task 4.2."""

from athena.render.renderer import format_report, render_markdown, resolve_placeholders
from athena.schemas import (
    ClaimType,
    Confidence,
    EvidenceRef,
    Finding,
    Metric,
    Recommendation,
    Report,
    ToolResult,
    ToolStatus,
    VerificationSummary,
)


def test_resolve_placeholders_success():
    tr = ToolResult(
        id="t1",
        tool="stats_test",
        status=ToolStatus.ok,
        metrics=[
            Metric(name="churn_rate", value=0.2678, unit=""),
            Metric(name="customer_count", value=5000, unit=""),
        ],
    )
    report = Report(
        question="What is the churn rate?",
        tldr="Analysis shows rate is {{t1.churn_rate}} across {{t1.customer_count}} users.",
        findings=[
            Finding(
                id="f1",
                text="The estimated churn rate is {{t1.churn_rate}}.",
                claim_type=ClaimType.descriptive,
                evidence=[EvidenceRef(tool_result_id="t1", metric="churn_rate")],
            )
        ],
        recommendations=[
            Recommendation(
                text="Focus on {{t1.customer_count}} users.",
                supported_by=["f1"],
                confidence=Confidence.high,
            )
        ],
        caveats=["Evaluated on {{t1.customer_count}} records."],
    )

    resolved = resolve_placeholders(report, [tr], decimal_places=2)

    assert "0.27" in resolved.tldr
    assert "5000" in resolved.tldr
    assert "0.27" in resolved.findings[0].text
    assert "5000" in resolved.recommendations[0].text
    assert "5000" in resolved.caveats[0]


def test_resolve_placeholders_unresolved_preserved():
    report = Report(
        question="Q",
        tldr="Value is {{t99.missing_metric}}.",
        findings=[],
    )
    resolved = resolve_placeholders(report, [])
    assert "{{t99.missing_metric}}" in resolved.tldr


def test_format_report_and_render_markdown():
    report = Report(
        question="What is customer retention?",
        tldr="Retention stands at 85%.",
        findings=[
            Finding(
                id="f1",
                text="85% stayed.",
                claim_type=ClaimType.descriptive,
                evidence=[EvidenceRef(tool_result_id="t1", metric="retention")],
            )
        ],
        recommendations=[
            Recommendation(
                text="Reward loyal users.",
                supported_by=["f1"],
                confidence=Confidence.high,
            )
        ],
        caveats=["Based on last quarter."],
    )

    summary = VerificationSummary(total_checks=5, passed=5, failed=0)
    md = render_markdown(report, summary)
    assert "# Analytical Report" in md
    assert "Retention stands at 85%." in md
    assert "🟢 PASS" in md
    assert "Reward loyal users." in md

    formatted_dict = format_report(report)
    assert isinstance(formatted_dict, dict)
    assert formatted_dict["question"] == "What is customer retention?"
