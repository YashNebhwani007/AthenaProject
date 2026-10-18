"""Tests for benchmark runner and scorer per Task 5.2."""

from pathlib import Path

import pytest

from athena.llm.base import LLMClient, LLMResponse, Usage
from benchmark.runner import run_benchmark
from benchmark.scorer import aggregate_scores, score_question


def test_scorer_numeric_within_tolerance():
    gt = {
        "question_id": "test_num",
        "expected_answer_type": "numeric",
        "expected_value": 100.0,
        "tolerance": {"type": "relative", "value": 0.05},
    }
    res = score_question({"expected_value": 102.0}, gt)
    assert res["passed"] is True


def test_scorer_numeric_outside_tolerance():
    gt = {
        "question_id": "test_num",
        "expected_answer_type": "numeric",
        "expected_value": 100.0,
        "tolerance": {"type": "relative", "value": 0.01},
    }
    res = score_question({"expected_value": 110.0}, gt)
    assert res["passed"] is False
    assert "outside tolerance" in res["issue"]


def test_scorer_refusal_detection():
    gt = {"question_id": "test_refusal", "expected_answer_type": "refusal", "answerable": False}
    res = score_question({"answerable": False, "reason": "Data not present"}, gt)
    assert res["passed"] is True

    res_fail = score_question({"answerable": True, "value": "123"}, gt)
    assert res_fail["passed"] is False


def test_scorer_leakage_detection():
    gt = {"question_id": "test_leak", "expected_answer_type": "leakage_detected"}
    res = score_question({"highest_severity": "high"}, gt)
    assert res["passed"] is True


def test_aggregate_scores_calculation():
    scores = [
        {"question_id": "q1", "passed": True, "answer_type": "numeric"},
        {"question_id": "q2", "passed": True, "answer_type": "refusal"},
        {"question_id": "q3", "passed": False, "answer_type": "numeric", "issue": "wrong"},
        {"question_id": "q4", "passed": True, "answer_type": "leakage_detected"},
    ]
    summary = aggregate_scores(scores)
    assert summary["total_questions"] == 4
    assert summary["passed"] == 3
    assert summary["failed"] == 1
    assert summary["accuracy"] == 0.75
    assert summary["refusal_accuracy"] == 1.0
    assert summary["leakage_recall"] == 1.0
    assert summary["hallucination_rate"] == 0.25


class MockBenchLLM(LLMClient):
    async def chat(self, messages: list[dict], tools=None, seed=None) -> LLMResponse:
        return LLMResponse(
            content='{"question": "What is churn?", "answerable": true, "tldr": "Churn is 0.26"}',
            usage=Usage(prompt_tokens=10, completion_tokens=10),
            is_final=True,
        )


@pytest.mark.asyncio
async def test_run_benchmark_mocked(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "benchmark.runner.create_llm_client",
        lambda _cfg: MockBenchLLM(),
    )

    results = await run_benchmark(
        systems=["A1"],
        repeats=1,
        question_filter="smoke",
        output_dir=tmp_path,
    )

    assert "A1" in results["summaries"]
    assert (tmp_path / "results.json").exists()
    assert (tmp_path / "results.md").exists()
    assert (tmp_path / "failure_analysis.md").exists()
    assert (tmp_path / "results.md").stat().st_size > 0
