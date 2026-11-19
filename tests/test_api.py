"""Tests for FastAPI backend application and API routes."""

import io
from pathlib import Path

import httpx
import pytest

from athena.api.main import app
from athena.api.routes import RUNS, SESSIONS
from athena.data import default_registry
from athena.llm.base import LLMClient, LLMResponse, Usage
from athena.schemas import Report, RunResult, VerificationSummary


class MockApiLLM(LLMClient):
    async def chat(self, messages: list[dict], tools=None, seed=None) -> LLMResponse:
        rep = Report(question="What is churn?", tldr="Churn is 25%", findings=[])
        return LLMResponse(
            content=f"```json\n{rep.model_dump_json()}\n```",
            usage=Usage(prompt_tokens=10, completion_tokens=10),
            is_final=True,
        )


@pytest.fixture
def client():
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health_check(client: httpx.AsyncClient):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "version": "0.2.0"}


@pytest.mark.asyncio
async def test_upload_dataset_and_profile(client: httpx.AsyncClient):
    csv_content = b"user_id,churn,spend\n1,0,50.0\n2,1,100.0\n3,0,25.0\n"
    files = {"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}

    res = await client.post("/api/datasets", files=files)
    assert res.status_code == 200
    data = res.json()
    assert "dataset_id" in data
    assert data["row_count"] == 3
    assert data["column_count"] == 3
    ds_id = data["dataset_id"]

    # Test profile endpoint
    res_prof = await client.get(f"/api/datasets/{ds_id}/profile")
    assert res_prof.status_code == 200
    assert "profile" in res_prof.json()


@pytest.mark.asyncio
async def test_demo_datasets(client: httpx.AsyncClient):
    res = await client.get("/api/demo-datasets")
    assert res.status_code == 200
    assert "datasets" in res.json()


@pytest.mark.asyncio
async def test_session_lifecycle_and_runs(client: httpx.AsyncClient, monkeypatch):
    monkeypatch.setattr("athena.agent.orchestrator.create_llm_client", lambda _c: MockApiLLM())

    csv_path = Path("tests/fixtures/test_data.csv").resolve()
    default_registry.register("session_test_ds", csv_path)

    # 1. Create session
    res_sess = await client.post("/api/sessions", json={"dataset_id": "session_test_ds"})
    assert res_sess.status_code == 200
    sess_id = res_sess.json()["session_id"]
    assert sess_id in SESSIONS

    # 2. Ask question via SSE stream
    res_ask = await client.post(
        f"/api/sessions/{sess_id}/ask",
        json={"question": "What is the churn rate?"},
    )
    assert res_ask.status_code == 200
    # Confirm streaming content type
    assert "text/event-stream" in res_ask.headers["content-type"]
    assert len(res_ask.text) > 0

    # 3. Store a mock run to test GET /api/runs/{id}
    mock_run = RunResult(
        run_id="run_test123",
        session_id=sess_id,
        question="What is churn?",
        report=Report(question="What is churn?", tldr="Done", findings=[]),
        verification=VerificationSummary(total_checks=0, passed=0, failed=0),
        trace=[],
        total_steps=1,
        total_tokens=20,
        total_runtime_ms=100.0,
    )
    RUNS["run_test123"] = mock_run

    res_run = await client.get("/api/runs/run_test123")
    assert res_run.status_code == 200
    assert res_run.json()["run_id"] == "run_test123"


@pytest.mark.asyncio
async def test_ask_question_auto_recovers_stale_session(client: httpx.AsyncClient, monkeypatch):
    """Verify ask endpoint auto-recovers session if session_id is missing from memory."""
    monkeypatch.setattr("athena.agent.orchestrator.create_llm_client", lambda _c: MockApiLLM())

    csv_path = Path("tests/fixtures/test_data.csv").resolve()
    default_registry.register("recover_test_ds", csv_path)

    # Use a non-existent session_id but pass dataset_id
    res_ask = await client.post(
        "/api/sessions/sess_stale_1234/ask",
        json={"question": "What is churn?", "dataset_id": "recover_test_ds"},
    )
    assert res_ask.status_code == 200
    assert "text/event-stream" in res_ask.headers["content-type"]
    assert "sess_stale_1234" in SESSIONS


@pytest.mark.asyncio
async def test_api_run_not_found(client: httpx.AsyncClient):
    """Verify requesting a non-existent run_id returns HTTP 404."""
    res = await client.get("/api/runs/non_existent_run_999")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_api_dataset_profile_not_found(client: httpx.AsyncClient):
    """Verify requesting a profile for a non-existent dataset returns HTTP 404."""
    res = await client.get("/api/datasets/completely_non_existent_ds/profile")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_api_create_session_missing_dataset_id_returns_422(client: httpx.AsyncClient):
    """Verify creating session with missing required dataset_id returns HTTP 422."""
    res = await client.post("/api/sessions", json={})
    assert res.status_code == 422
