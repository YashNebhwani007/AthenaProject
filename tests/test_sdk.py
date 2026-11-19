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
