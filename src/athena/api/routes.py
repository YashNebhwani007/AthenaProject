"""FastAPI routes for dataset ingestion, profiling, sessions, and SSE analytics streaming."""

import asyncio
import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from athena.agent.orchestrator import Orchestrator
from athena.config import settings
from athena.data import default_registry
from athena.logging import get_logger
from athena.schemas import RunResult
from athena.tools.profile import profile_dataset

logger = get_logger(__name__)
router = APIRouter(prefix="/api")

# In-memory storage for active sessions and completed runs
SESSIONS: dict[str, dict[str, Any]] = {}
RUNS: dict[str, RunResult] = {}


class CreateSessionRequest(BaseModel):
    dataset_id: str


class AskQuestionRequest(BaseModel):
    question: str
    dataset_id: str | None = None


@router.post("/datasets")
async def upload_dataset(file: UploadFile = File(...)) -> dict[str, Any]:
    """Upload CSV or Parquet dataset file, register with DuckDB, and return profile."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".csv", ".parquet"):
        raise HTTPException(status_code=400, detail="Only CSV and Parquet files are supported")

    upload_dir = Path(settings.data_dir) / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    dataset_id = f"ds_{uuid.uuid4().hex[:8]}"
    save_path = upload_dir / f"{dataset_id}{suffix}"

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    handle = default_registry.register(dataset_id=dataset_id, file_path=save_path)
    profile = await profile_dataset(dataset_id=dataset_id, registry=default_registry)

    return {
        "dataset_id": dataset_id,
        "filename": file.filename,
        "row_count": handle.row_count,
        "column_count": handle.column_count,
        "profile": profile.output,
    }


@router.get("/datasets/{dataset_id}/profile")
async def get_dataset_profile(dataset_id: str) -> dict[str, Any]:
    """Retrieve full exploratory profile and data quality warnings for a dataset."""
    if dataset_id not in default_registry:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")
    profile = await profile_dataset(dataset_id=dataset_id, registry=default_registry)
    return {"dataset_id": dataset_id, "profile": profile.output}


@router.get("/demo-datasets")
def list_demo_datasets() -> dict[str, Any]:
    """List pre-packaged demo datasets from benchmark manifest."""
    manifest_path = Path("benchmark/datasets/manifest.json")
    if not manifest_path.exists():
        return {"datasets": []}

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    # Register demo datasets with default_registry if not already registered
    for ds in manifest.get("datasets", []):
        ds_id = ds["id"]
        csv_path = Path(ds["path"])
        if csv_path.exists() and ds_id not in default_registry:
            default_registry.register(dataset_id=ds_id, file_path=csv_path)

    return manifest


@router.post("/sessions")
def create_session(req: CreateSessionRequest) -> dict[str, Any]:
    """Create a new analytical session associated with a dataset."""
    if req.dataset_id not in default_registry:
        manifest_path = Path("benchmark/datasets/manifest.json")
        if manifest_path.exists():
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
            for ds in manifest.get("datasets", []):
                if ds["id"] == req.dataset_id:
                    csv_path = Path(ds["path"])
                    if csv_path.exists():
                        default_registry.register(dataset_id=ds["id"], file_path=csv_path)
                        break

    if req.dataset_id not in default_registry:
        raise HTTPException(status_code=404, detail=f"Dataset '{req.dataset_id}' not found")

    session_id = f"sess_{uuid.uuid4().hex[:8]}"
    SESSIONS[session_id] = {
        "session_id": session_id,
        "dataset_id": req.dataset_id,
    }
    return SESSIONS[session_id]


@router.post("/sessions/{session_id}/ask")
async def ask_question(
    session_id: str,
    req: AskQuestionRequest,
) -> EventSourceResponse:
    """Stream live analytical trace events and final decision report via SSE."""
    if session_id not in SESSIONS:
        # Auto-recover session if dataset_id provided or can be resolved
        ds_id = req.dataset_id
        if not ds_id or ds_id not in default_registry:
            manifest_path = Path("benchmark/datasets/manifest.json")
            if manifest_path.exists():
                with open(manifest_path, encoding="utf-8") as f:
                    manifest = json.load(f)
                for ds in manifest.get("datasets", []):
                    csv_path = Path(ds["path"])
                    if csv_path.exists() and ds["id"] not in default_registry:
                        default_registry.register(dataset_id=ds["id"], file_path=csv_path)
            if ds_id and ds_id in default_registry:
                pass
            elif default_registry:
                ds_id = next(iter(default_registry))

        if ds_id and ds_id in default_registry:
            SESSIONS[session_id] = {
                "session_id": session_id,
                "dataset_id": ds_id,
            }
            logger.info("session_auto_recovered", session_id=session_id, dataset_id=ds_id)
        else:
            raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    dataset_id = SESSIONS[session_id]["dataset_id"]
    event_queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()

    async def on_event(ev: dict[str, Any]) -> None:
        await event_queue.put(ev)

    async def run_task() -> None:
        try:
            orch = Orchestrator(registry=default_registry)
            run_result = await orch.run(
                question=req.question,
                dataset_id=dataset_id,
                session_id=session_id,
                event_callback=on_event,
            )
            RUNS[run_result.run_id] = run_result
        except Exception as exc:
            logger.error("ask_question_failed", error=str(exc))
            await event_queue.put({"event": "error", "data": {"error": str(exc)}})
        finally:
            await event_queue.put(None)  # Signal completion

    asyncio.create_task(run_task())

    async def event_generator():
        while True:
            msg = await event_queue.get()
            if msg is None:
                break
            yield {
                "event": msg["event"],
                "data": json.dumps(msg["data"], default=str),
            }

    return EventSourceResponse(event_generator())


@router.get("/runs/{run_id}")
def get_run(run_id: str) -> dict[str, Any]:
    """Fetch completed run telemetry, execution trace, and verified report."""
    if run_id not in RUNS:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    return RUNS[run_id].model_dump()


@router.get("/benchmark/results")
def get_benchmark_results() -> dict[str, Any]:
    """Fetch latest compiled benchmark evaluation results."""
    res_path = Path("benchmark/results/results.json")
    if not res_path.exists():
        return {"error": "Benchmark results not yet generated"}
    with open(res_path, encoding="utf-8") as f:
        return json.load(f)
