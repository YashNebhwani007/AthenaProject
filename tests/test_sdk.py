"""Unit tests for Athena Python SDK client."""

import httpx
import pytest

from athena.api.main import app
from athena.sdk import AthenaClient


@pytest.mark.asyncio
async def test_sdk_client_initialization_defaults():
    client = AthenaClient()
    assert client.base_url == "http://localhost:8000"
    assert client.api_key is None
    await client.close()


@pytest.mark.asyncio
async def test_sdk_client_custom_url_and_auth():
    client = AthenaClient(base_url="https://athena.example.com/", api_key="secret-token-123")
    assert client.base_url == "https://athena.example.com"
    assert client.api_key == "secret-token-123"
    assert client._client.headers["Authorization"] == "Bearer secret-token-123"
    await client.close()


@pytest.mark.asyncio
async def test_sdk_client_context_manager():
    async with AthenaClient(base_url="http://testserver") as client:
        assert client.base_url == "http://testserver"


@pytest.mark.asyncio
async def test_sdk_upload_dataset(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")

    transport = httpx.ASGITransport(app=app)
    client = AthenaClient(base_url="http://testserver")
    client._client = httpx.AsyncClient(transport=transport, base_url="http://testserver")
    try:
        res = await client.upload_dataset(csv_file)
        assert "dataset_id" in res
        assert res["row_count"] == 2
        assert res["column_count"] == 2
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_sdk_ask_stream_parsing():
    def mock_handler(request: httpx.Request) -> httpx.Response:
        content = (
            b"event: status\r\n"
            b'data: {"step": "planning"}\r\n\r\n'
            b"event: result\r\n"
            b'data: {"answer": 42}\r\n\r\n'
        )
        return httpx.Response(200, content=content, headers={"Content-Type": "text/event-stream"})

    transport = httpx.MockTransport(mock_handler)
    client = AthenaClient(base_url="http://testserver")
    client._client = httpx.AsyncClient(transport=transport, base_url="http://testserver")
    try:
        events = []
        async for event in client.ask_stream(session_id="sess_123", question="Test?"):
            events.append(event)
        assert len(events) == 2
        assert events[0]["event"] == "status"
        assert events[0]["data"] == {"step": "planning"}
        assert events[1]["event"] == "result"
        assert events[1]["data"] == {"answer": 42}
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_sdk_error_handling_http_status():
    def mock_handler(request: httpx.Request) -> httpx.Response:
        if "nonexistent" in request.url.path:
            return httpx.Response(404, json={"detail": "Dataset not found"})
        return httpx.Response(500, json={"detail": "Internal server error"})

    transport = httpx.MockTransport(mock_handler)
    client = AthenaClient(base_url="http://testserver")
    client._client = httpx.AsyncClient(transport=transport, base_url="http://testserver")
    try:
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.get_profile("nonexistent")
        assert exc_info.value.response.status_code == 404

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.get_run("run_err")
        assert exc_info.value.response.status_code == 500
    finally:
        await client.close()
