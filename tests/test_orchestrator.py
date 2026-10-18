"""Tests for Orchestrator autonomous loop with mocked LLM."""

from pathlib import Path
from typing import Any

import pytest

from athena.agent.orchestrator import Orchestrator
from athena.config import Settings
from athena.data import DatasetRegistry
from athena.llm.base import LLMClient, LLMResponse, ToolCall, Usage
from athena.schemas import ClaimType, EvidenceRef, Finding, Report, RunResult


class MockSequenceLLM(LLMClient):
    """Mock LLM returning a pre-defined sequence of responses."""

    def __init__(self, responses: list[LLMResponse]) -> None:
        self.responses = responses
        self.call_idx = 0
        self.recorded_messages: list[list[dict[str, Any]]] = []

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        seed: int | None = None,
    ) -> LLMResponse:
        self.recorded_messages.append(messages)
        if self.call_idx < len(self.responses):
            resp = self.responses[self.call_idx]
            self.call_idx += 1
            return resp
        # Default empty completion
        return LLMResponse(content="{}", is_final=True)


@pytest.fixture
def dataset_registry() -> DatasetRegistry:
    fixture_path = Path(__file__).parent / "fixtures" / "test_data.csv"
    reg = DatasetRegistry()
    reg.register(dataset_id="orch_test", file_path=fixture_path, table_name="customers")
    return reg


@pytest.mark.asyncio
async def test_orchestrator_end_to_end_flow(dataset_registry: DatasetRegistry):
    """Verify Orchestrator auto-profiles, dispatches tools, and parses Report JSON."""
    final_report = Report(
        question="What is the churn rate?",
        answerable=True,
        tldr="The churn rate is 26.5% across 100 customer records.",
        findings=[
            Finding(
                id="f1",
                text="Overall customer churn rate is 26.5%.",
                claim_type=ClaimType.descriptive,
                evidence=[EvidenceRef(tool_result_id="t2", metric="total_rows")],
            )
        ],
        caveats=["Data is from test fixture."],
        recommendations=[],
    )

    mock_llm = MockSequenceLLM([
        # Step 1: LLM requests run_sql
        LLMResponse(
            content="Running SQL query to compute churn rate.",
            tool_calls=[
                ToolCall(
                    id="call_sql_1",
                    name="run_sql",
                    arguments={"query": "SELECT count(*), avg(churn) FROM customers"},
                )
            ],
            usage=Usage(prompt_tokens=100, completion_tokens=30),
            is_final=False,
        ),
        # Step 2: LLM provides final Report JSON
        LLMResponse(
            content=f"```json\n{final_report.model_dump_json()}\n```",
            tool_calls=[],
            usage=Usage(prompt_tokens=200, completion_tokens=80),
            is_final=True,
        ),
    ])

    orchestrator = Orchestrator(llm_client=mock_llm, registry=dataset_registry)
    result = await orchestrator.run(
        question="What is the churn rate?",
        dataset_id="orch_test",
    )

    assert isinstance(result, RunResult)
    assert result.question == "What is the churn rate?"
    assert result.report is not None
    assert result.report.answerable is True
    assert "26.5%" in result.report.tldr
    assert len(result.report.findings) == 1

    # Verify trace contains initial profile + run_sql execution
    assert len(result.trace) >= 2
    assert result.trace[0].tool == "profile"
    assert result.trace[1].tool == "run_sql"
    assert result.total_steps == 2
    assert result.total_tokens == 410

    # Verify verification summary populated (Task 4.3)
    assert result.verification.total_checks > 0
    assert result.verification.passed > 0


@pytest.mark.asyncio
async def test_orchestrator_loop_detection(dataset_registry: DatasetRegistry):
    """Verify repeated identical tool calls are intercepted by loop detector."""
    repeated_call = LLMResponse(
        content="Running identical query again.",
        tool_calls=[
            ToolCall(
                id="loop_call",
                name="run_sql",
                arguments={"query": "SELECT 1"},
            )
        ],
        usage=Usage(prompt_tokens=50, completion_tokens=10),
        is_final=False,
    )

    # Repeat same call 4 times, then finalize
    mock_llm = MockSequenceLLM([
        repeated_call,
        repeated_call,
        repeated_call,
        LLMResponse(content='{"question": "test", "tldr": "Done"}', is_final=True),
    ])

    orchestrator = Orchestrator(llm_client=mock_llm, registry=dataset_registry)
    result = await orchestrator.run(question="Loop check", dataset_id="orch_test")

    # Confirm run finishes safely without hanging
    assert result.total_steps >= 3
    assert result.report is not None


@pytest.mark.asyncio
async def test_orchestrator_budget_exhaustion(dataset_registry: DatasetRegistry):
    """Verify orchestrator halts loop when step budget is reached."""
    infinite_tool_calls = MockSequenceLLM([
        LLMResponse(
            content="Tool call step",
            tool_calls=[
                ToolCall(id=f"c_{i}", name="run_sql", arguments={"query": f"SELECT {i}"})
            ],
            usage=Usage(prompt_tokens=20, completion_tokens=5),
            is_final=False,
        )
        for i in range(10)
    ])

    strict_cfg = Settings(max_steps=2)
    orchestrator = Orchestrator(
        llm_client=infinite_tool_calls,
        registry=dataset_registry,
        app_settings=strict_cfg,
    )

    result = await orchestrator.run(question="Budget test", dataset_id="orch_test")
    assert result.total_steps <= 3


@pytest.mark.asyncio
async def test_orchestrator_event_callback(dataset_registry: DatasetRegistry):
    """Verify orchestrator streams events (tool_result, report_draft, verification, final)."""
    mock_llm = MockSequenceLLM([
        LLMResponse(
            content='{"question": "Q?", "tldr": "Done", "findings": []}',
            is_final=True,
        )
    ])
    events = []

    async def on_event(ev: dict[str, Any]) -> None:
        events.append(ev)

    orchestrator = Orchestrator(llm_client=mock_llm, registry=dataset_registry)
    await orchestrator.run(
        question="Q?",
        dataset_id="orch_test",
        event_callback=on_event,
    )
    event_names = [e["event"] for e in events]
    assert "tool_result" in event_names
    assert "report_draft" in event_names
    assert "verification" in event_names
    assert "final" in event_names

