"""Tests for Athena core schemas."""

import json

from athena.schemas import (
    Artifact,
    ClaimType,
    Confidence,
    EventType,
    EvidenceRef,
    Finding,
    Metric,
    Recommendation,
    Report,
    RunResult,
    ToolResult,
    ToolStatus,
    VerificationResult,
    VerificationSummary,
)


def test_tool_result_serialization_and_defaults():
    """Verify ToolResult model defaults and JSON serialization round-trip."""
    result = ToolResult(
        id="t1",
        tool="run_sql",
        args={"query": "SELECT count(*) FROM t"},
        output={"count": 42},
        metrics=[Metric(name="row_count", value=42, unit="rows")],
        artifacts=[Artifact(type="table", ref="data/cache/t1.parquet")],
    )

    assert result.status == ToolStatus.ok
    assert result.runtime_ms == 0.0
    assert result.warnings == []

    raw_json = result.model_dump_json()
    loaded = ToolResult.model_validate_json(raw_json)
    assert loaded == result
    assert loaded.metrics[0].value == 42


def test_report_and_finding_structures():
    """Verify Report, Finding, and Recommendation hierarchy and validation."""
    finding = Finding(
        id="f1",
        text="Average churn rate is 26.5% across subscribers.",
        claim_type=ClaimType.descriptive,
        evidence=[EvidenceRef(tool_result_id="t1", metric="churn_rate")],
    )

    rec = Recommendation(
        text="Target high-tenure fiber optic customers with retention discounts.",
        supported_by=["f1"],
        confidence=Confidence.high,
    )

    report = Report(
        question="What is the customer churn profile?",
        answerable=True,
        tldr="Overall churn is 26.5%, driven primarily by month-to-month contracts.",
        findings=[finding],
        caveats=["Assumes tenure is measured in full calendar months."],
        recommendations=[rec],
    )

    data = report.model_dump()
    assert data["answerable"] is True
    assert data["findings"][0]["id"] == "f1"
    assert data["recommendations"][0]["confidence"] == "high"

    rebuilt = Report.model_validate(data)
    assert rebuilt == report


def test_verification_summary():
    """Verify VerificationSummary serialization and details listing."""
    v_item = VerificationResult(
        rule="V1_numeric_grounding",
        finding_id="f1",
        passed=True,
    )
    summary = VerificationSummary(
        total_checks=1,
        passed=1,
        failed=0,
        unverified_claims=0,
        repairs_attempted=0,
        details=[v_item],
    )

    dumped = json.loads(summary.model_dump_json())
    assert dumped["passed"] == 1
    assert dumped["details"][0]["rule"] == "V1_numeric_grounding"


def test_run_result_roundtrip():
    """Verify RunResult holds report, trace, telemetry, and serializes."""
    run = RunResult(
        run_id="run-123",
        session_id="session-456",
        question="What is the churn rate?",
        trace=[
            ToolResult(id="t1", tool="profile", status=ToolStatus.ok),
        ],
        total_steps=2,
        total_tokens=1500,
        total_runtime_ms=1240.5,
    )

    assert run.created_at is not None
    json_str = run.model_dump_json()
    reconstructed = RunResult.model_validate_json(json_str)
    assert reconstructed.run_id == "run-123"
    assert len(reconstructed.trace) == 1
    assert reconstructed.trace[0].tool == "profile"


def test_enum_members():
    """Verify enum members exist as expected."""
    assert ClaimType.statistical == "statistical"
    assert Confidence.low == "low"
    assert ToolStatus.error == "error"
    assert EventType.step_started == "step_started"
    assert EventType.clarification_needed == "clarification_needed"


def test_finding_normalization_statement_and_missing_claim_type():
    """Verify Finding normalizes 'statement' to 'text' and defaults 'claim_type'."""
    raw = {
        "id": "f1",
        "statement": "The overall passenger survival rate was 38.4%.",
    }
    finding = Finding.model_validate(raw)
    assert finding.id == "f1"
    assert finding.text == "The overall passenger survival rate was 38.4%."
    assert finding.claim_type == ClaimType.descriptive
    assert finding.evidence == []


def test_evidenceref_normalization_string():
    """Verify EvidenceRef normalizes string representations like 't1.metric' or raw strings."""
    ref1 = EvidenceRef.model_validate("titanic_analysis.survival_rate")
    assert ref1.tool_result_id == "titanic_analysis"
    assert ref1.metric == "survival_rate"

    ref2 = EvidenceRef.model_validate("survival_rate")
    assert ref2.tool_result_id == ""
    assert ref2.metric == "survival_rate"

    finding = Finding.model_validate({
        "id": "f1",
        "text": "Survival was high.",
        "evidence": ["titanic_analysis.survival_rate", "t2.count"],
    })
    assert len(finding.evidence) == 2
    assert finding.evidence[0].tool_result_id == "titanic_analysis"
    assert finding.evidence[0].metric == "survival_rate"
    assert finding.evidence[1].tool_result_id == "t2"
    assert finding.evidence[1].metric == "count"


def test_report_normalization_nested_and_aliases():
    """Verify Report handles nested 'report' key, summary alias, and string items."""
    raw = {
        "report": {
            "question": "What was the survival rate?",
            "summary": "Survival was approximately 38.4%.",
            "findings": [
                {
                    "id": "f1",
                    "claim": "Females survived at higher rates.",
                }
            ],
            "caveats": "Small sample in some cabins.",
            "recommendations": [
                {
                    "action": "Ensure lifeboats prioritize safety.",
                    "confidence": "high",
                }
            ],
        }
    }
    report = Report.model_validate(raw)
    assert report.question == "What was the survival rate?"
    assert report.tldr == "Survival was approximately 38.4%."
    assert len(report.findings) == 1
    assert report.findings[0].text == "Females survived at higher rates."
    assert report.findings[0].claim_type == ClaimType.descriptive
    assert report.caveats == ["Small sample in some cabins."]
    assert len(report.recommendations) == 1
    assert report.recommendations[0].text == "Ensure lifeboats prioritize safety."
    assert report.recommendations[0].confidence == Confidence.high
