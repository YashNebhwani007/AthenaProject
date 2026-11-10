"""Tests for Verifier coordinator and repair loop per Task 4.2."""

import pytest

from athena.config import Settings
from athena.llm.base import LLMClient, LLMResponse, Usage
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
)
from athena.verify.verifier import Verifier


class MockRepairLLM(LLMClient):
    """Mocks LLM repair response by returning corrected Report JSON."""

    def __init__(self, corrected_report: Report) -> None:
        self.corrected_report = corrected_report
        self.call_count = 0

    async def chat(self, messages: list[dict], tools=None, seed=None) -> LLMResponse:
        self.call_count += 1
        return LLMResponse(
            content=f"```json\n{self.corrected_report.model_dump_json()}\n```",
            usage=Usage(prompt_tokens=100, completion_tokens=80),
        )


@pytest.mark.asyncio
async def test_verifier_passes_valid_report():
    verifier = Verifier()
    tr = ToolResult(
        id="t1",
        tool="stats_test",
        status=ToolStatus.ok,
        metrics=[Metric(name="mean_diff", value=10.0, unit="")],
    )
    report = Report(
        question="Q",
        tldr="Analysis TLDR",
        findings=[
            Finding(
                id="f1",
                text="Group A is higher.",
                claim_type=ClaimType.comparative,
                evidence=[EvidenceRef(tool_result_id="t1", metric="mean_diff")],
            )
        ],
        recommendations=[
            Recommendation(text="Action item", supported_by=["f1"], confidence=Confidence.high)
        ],
    )

    final_report, summary = await verifier.verify(report, [tr])
    assert summary.failed == 0
    assert summary.passed > 0
    assert summary.repairs_attempted == 0
    assert summary.unverified_claims == 0


@pytest.mark.asyncio
async def test_verifier_triggers_repair_loop_and_succeeds():
    settings = Settings(max_repair_iterations=2)
    verifier = Verifier(app_settings=settings)

    tr = ToolResult(
        id="t1",
        tool="stats_test",
        status=ToolStatus.ok,
        metrics=[Metric(name="mean_diff", value=10.0, unit="")],
    )

    # Initial flawed report with causal keyword on comparative claim
    flawed_report = Report(
        question="Q",
        tldr="Flawed TLDR",
        findings=[
            Finding(
                id="f1",
                text="Treatment causes higher sales.",  # Causal violation
                claim_type=ClaimType.comparative,
                evidence=[EvidenceRef(tool_result_id="t1", metric="mean_diff")],
            )
        ],
        recommendations=[
            Recommendation(text="Action item", supported_by=["f1"], confidence=Confidence.high)
        ],
    )

    # Corrected report
    corrected_report = Report(
        question="Q",
        tldr="Corrected TLDR",
        findings=[
            Finding(
                id="f1",
                text="Treatment is associated with higher sales.",
                claim_type=ClaimType.comparative,
                evidence=[EvidenceRef(tool_result_id="t1", metric="mean_diff")],
            )
        ],
        recommendations=[
            Recommendation(text="Action item", supported_by=["f1"], confidence=Confidence.high)
        ],
    )

    mock_llm = MockRepairLLM(corrected_report)
    final_report, summary = await verifier.verify(flawed_report, [tr], llm_client=mock_llm)

    assert mock_llm.call_count == 1
    assert summary.repairs_attempted == 1
    assert summary.failed == 0
    assert "associated with" in final_report.findings[0].text


@pytest.mark.asyncio
async def test_verifier_degrades_when_unfixable():
    settings = Settings(max_repair_iterations=1)
    verifier = Verifier(app_settings=settings)

    tr = ToolResult(
        id="t1",
        tool="stats_test",
        status=ToolStatus.ok,
        metrics=[Metric(name="p_value", value=0.45, unit="")],
    )

    # Flawed report asserting significance with p=0.45
    flawed_report = Report(
        question="Q",
        tldr="Flawed",
        findings=[
            Finding(
                id="f1",
                text="There is a statistically significant difference.",
                claim_type=ClaimType.statistical,
                evidence=[EvidenceRef(tool_result_id="t1", metric="p_value")],
            )
        ],
        recommendations=[
            Recommendation(text="Action", supported_by=["f1"], confidence=Confidence.low)
        ],
    )

    # LLM fails to fix it and returns the same flawed report
    mock_llm = MockRepairLLM(flawed_report)
    final_report, summary = await verifier.verify(flawed_report, [tr], llm_client=mock_llm)

    assert summary.repairs_attempted == 1
    assert summary.failed > 0
    assert summary.unverified_claims > 0
    assert final_report.findings[0].text.startswith("[UNVERIFIED]")
    assert any("Unverified claim in f1" in c for c in final_report.caveats)


class RawJsonRepairLLM(LLMClient):
    """Mocks LLM returning raw JSON text containing field aliases."""

    def __init__(self, raw_json: str) -> None:
        self.raw_json = raw_json
        self.call_count = 0

    async def chat(self, messages: list[dict], tools=None, seed=None) -> LLMResponse:
        self.call_count += 1
        return LLMResponse(
            content=self.raw_json,
            usage=Usage(prompt_tokens=100, completion_tokens=80),
        )


@pytest.mark.asyncio
async def test_verifier_repair_handles_statement_alias_and_missing_claim_type():
    """Verify repair loop handles LLM response using 'statement' and omitting 'claim_type'."""
    settings = Settings(max_repair_iterations=2)
    verifier = Verifier(app_settings=settings)

    tr = ToolResult(
        id="t1",
        tool="stats_test",
        status=ToolStatus.ok,
        metrics=[Metric(name="mean_diff", value=10.0, unit="")],
    )

    flawed_report = Report(
        question="Q",
        tldr="Flawed",
        findings=[
            Finding(
                id="f1",
                text="Treatment causes higher sales.",  # Causal violation
                claim_type=ClaimType.comparative,
                evidence=[EvidenceRef(tool_result_id="t1", metric="mean_diff")],
            )
        ],
        recommendations=[
            Recommendation(text="Action", supported_by=["f1"], confidence=Confidence.high)
        ],
    )

    # Simulated response from LLM using 'statement' and omitting 'claim_type'
    raw_response = """
    ```json
    {
      "question": "Q",
      "tldr": "Corrected summary",
      "findings": [
        {
          "id": "f1",
          "statement": "Treatment is associated with higher sales.",
          "evidence": [{"tool_result_id": "t1", "metric": "mean_diff"}]
        }
      ],
      "recommendations": [
        {
          "text": "Action item",
          "supported_by": ["f1"],
          "confidence": "high"
        }
      ]
    }
    ```
    """

    mock_llm = RawJsonRepairLLM(raw_response)
    final_report, summary = await verifier.verify(flawed_report, [tr], llm_client=mock_llm)

    assert mock_llm.call_count == 1
    assert summary.repairs_attempted == 1
    assert summary.failed == 0
    assert final_report.findings[0].text == "Treatment is associated with higher sales."
    assert final_report.findings[0].claim_type == ClaimType.descriptive
