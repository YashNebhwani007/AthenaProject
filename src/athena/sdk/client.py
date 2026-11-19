"""Asynchronous Python client SDK for Athena API."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import httpx


class AthenaClient:
    """Asynchronous client for interacting with Athena REST and SSE endpoints."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout,
        )

    async def __aenter__(self) -> AthenaClient:
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        await self.close()

    async def close(self) -> None:
        """Close underlying HTTP transport session."""
        await self._client.aclose()

    async def check_health(self) -> dict[str, str]:
        """Check API server health status."""
        resp = await self._client.get("/health")
        resp.raise_for_status()
        return resp.json()

    async def upload_dataset(self, file_path: str | Path) -> dict[str, Any]:
        """Upload a CSV or Parquet dataset file and register with Athena."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Dataset file not found: {path}")

        with open(path, "rb") as f:
            files = {"file": (path.name, f, "application/octet-stream")}
            resp = await self._client.post("/api/datasets", files=files)
            resp.raise_for_status()
            return resp.json()

    async def get_profile(self, dataset_id: str) -> dict[str, Any]:
        """Retrieve dataset profile and column statistics."""
        resp = await self._client.get(f"/api/datasets/{dataset_id}/profile")
        resp.raise_for_status()
        return resp.json()

    async def get_run(self, run_id: str) -> dict[str, Any]:
        """Retrieve execution results and report for a completed run."""
        resp = await self._client.get(f"/api/runs/{run_id}")
        resp.raise_for_status()
        return resp.json()

    async def create_session(self, dataset_id: str) -> dict[str, Any]:
        """Create a new analytical session for a dataset."""
        resp = await self._client.post("/api/sessions", json={"dataset_id": dataset_id})
        resp.raise_for_status()
        return resp.json()

    async def ask_stream(
        self, session_id: str, question: str
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream analytical execution events from session."""
        import json

        async with self._client.stream(
            "POST",
            f"/api/sessions/{session_id}/ask",
            json={"question": question},
            timeout=120.0,
        ) as response:
            response.raise_for_status()
            current_event = "message"
            async for line in response.aiter_lines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith("event:"):
                    current_event = line.replace("event:", "", 1).strip()
                elif line.startswith("data:"):
                    raw_data = line.replace("data:", "", 1).strip()
                    try:
                        parsed = json.loads(raw_data)
                    except json.JSONDecodeError:
                        parsed = raw_data
                    yield {"event": current_event, "data": parsed}
