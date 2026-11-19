"""Asynchronous Python client SDK for Athena API."""

from __future__ import annotations

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
