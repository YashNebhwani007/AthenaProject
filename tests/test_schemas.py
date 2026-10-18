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
