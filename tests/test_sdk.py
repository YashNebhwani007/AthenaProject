"""Unit tests for Athena Python SDK client."""

import pytest

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
