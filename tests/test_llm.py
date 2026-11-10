"""Tests for Athena LLM client, Groq integration, and response caching."""

import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from athena.config import Settings
from athena.llm import (
    CachedLLMClient,
    GroqClient,
    LLMClient,
    LLMResponse,
    Usage,
    create_llm_client,
)


class MockLLMClient(LLMClient):
    """Simple in-memory test double for LLMClient."""

    def __init__(self, responses: list[LLMResponse] | None = None) -> None:
        self.responses = responses or [
            LLMResponse(
                content="Default mocked answer",
                usage=Usage(prompt_tokens=10, completion_tokens=5),
            )
        ]
        self.call_count = 0
        self.last_messages: list[dict[str, Any]] = []

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        seed: int | None = None,
    ) -> LLMResponse:
        self.call_count += 1
        self.last_messages = messages
        idx = min(self.call_count - 1, len(self.responses) - 1)
        return self.responses[idx]


@pytest.mark.asyncio
async def test_groq_client_parsing():
    """Verify GroqClient parses OpenAI/Groq JSON completions and tool calls."""
    sample_response = {
        "choices": [
            {
                "message": {
                    "content": "Analyzing dataset now.",
                    "tool_calls": [
                        {
                            "id": "call_123",
                            "type": "function",
                            "function": {
                                "name": "run_sql",
                                "arguments": json.dumps({"query": "SELECT count(*) FROM table"}),
                            },
                        }
                    ],
                }
            }
        ],
        "usage": {
            "prompt_tokens": 150,
            "completion_tokens": 40,
            "total_tokens": 190,
        },
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=sample_response)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        groq = GroqClient(api_key="mock_key", client=client)
        resp = await groq.chat(
            messages=[{"role": "user", "content": "Query"}],
            tools=[{"type": "function", "function": {"name": "run_sql"}}],
        )

        assert resp.content == "Analyzing dataset now."
        assert len(resp.tool_calls) == 1
        assert resp.tool_calls[0].id == "call_123"
        assert resp.tool_calls[0].name == "run_sql"
        assert resp.tool_calls[0].arguments == {"query": "SELECT count(*) FROM table"}
        assert resp.usage.prompt_tokens == 150
        assert resp.usage.completion_tokens == 40
        assert resp.is_final is False


@pytest.mark.asyncio
async def test_groq_client_retry_on_429():
    """Verify GroqClient retries upon receiving HTTP 429."""
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(429, headers={"Retry-After": "0.01"})
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "Success after rate limit"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        groq = GroqClient(api_key="mock_key", max_retries=2, client=client)
        resp = await groq.chat(messages=[{"role": "user", "content": "Hi"}])
        assert resp.content == "Success after rate limit"
        assert attempts == 2


@pytest.mark.asyncio
async def test_cached_llm_client_record_and_replay(tmp_path: Path):
    """Verify CachedLLMClient correctly records and replays responses."""
    inner = MockLLMClient(
        [LLMResponse(content="First run result", usage=Usage(prompt_tokens=5, completion_tokens=3))]
    )

    cache_dir = tmp_path / "test_cache"

    # 1. Record mode
    recording_client = CachedLLMClient(
        inner_client=inner,
        cache_mode="record",
        cache_dir=cache_dir,
    )
    resp1 = await recording_client.chat(messages=[{"role": "user", "content": "What is 2+2?"}])
    assert resp1.content == "First run result"
    assert inner.call_count == 1

    # Check cache file was created
    cache_files = list(cache_dir.glob("*.json"))
    assert len(cache_files) == 1

    # 2. Replay mode
    replay_client = CachedLLMClient(
        inner_client=inner,
        cache_mode="replay",
        cache_dir=cache_dir,
    )
    resp2 = await replay_client.chat(messages=[{"role": "user", "content": "What is 2+2?"}])
    assert resp2.content == "First run result"
    # Call count did not increase
    assert inner.call_count == 1


@pytest.mark.asyncio
async def test_cached_llm_client_replay_miss_raises(tmp_path: Path):
    """Verify replay mode raises FileNotFoundError when key is not cached."""
    inner = MockLLMClient()
    replay_client = CachedLLMClient(
        inner_client=inner,
        cache_mode="replay",
        cache_dir=tmp_path / "empty_cache",
    )
    with pytest.raises(FileNotFoundError):
        await replay_client.chat(messages=[{"role": "user", "content": "Uncached question"}])


@pytest.mark.asyncio
async def test_cached_llm_client_auto_mode(tmp_path: Path):
    """Verify auto mode fetches on miss and replays on hit."""
    inner = MockLLMClient(
        [LLMResponse(content="Auto answer", usage=Usage(prompt_tokens=8, completion_tokens=4))]
    )
    auto_client = CachedLLMClient(
        inner_client=inner,
        cache_mode="auto",
        cache_dir=tmp_path / "auto_cache",
    )

    # First call: miss, queries inner
    resp1 = await auto_client.chat(messages=[{"role": "user", "content": "Tell me a joke"}])
    assert resp1.content == "Auto answer"
    assert inner.call_count == 1

    # Second call: hit, does not query inner
    resp2 = await auto_client.chat(messages=[{"role": "user", "content": "Tell me a joke"}])
    assert resp2.content == "Auto answer"
    assert inner.call_count == 1


def test_create_llm_client_factory():
    """Verify create_llm_client factory respects cache settings."""
    cfg_off = Settings(llm_cache_mode="off")
    client_off = create_llm_client(cfg_off)
    assert isinstance(client_off, GroqClient)

    cfg_auto = Settings(llm_cache_mode="auto")
    client_auto = create_llm_client(cfg_auto)
    assert isinstance(client_auto, CachedLLMClient)

    cfg_demo = Settings(demo_mode=True)
    client_demo = create_llm_client(cfg_demo)
    from athena.llm.demo_client import DemoLLMClient

    assert isinstance(client_demo, DemoLLMClient)
