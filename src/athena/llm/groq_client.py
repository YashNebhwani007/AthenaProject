"""Groq API client implementation using httpx."""

import asyncio
import json
import random
from typing import Any

import httpx

from athena.llm.base import LLMClient, LLMResponse, ToolCall, Usage
from athena.logging import get_logger

logger = get_logger(__name__)


class GroqClient(LLMClient):
    """Client for Groq's OpenAI-compatible chat completions API."""

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        base_url: str = "https://api.groq.com/openai/v1",
        max_retries: int = 3,
        default_seed: int = 42,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.default_seed = default_seed
        self._external_client = client is not None
        self._client = client or httpx.AsyncClient(timeout=60.0)

    async def close(self) -> None:
        """Close HTTP client if created internally."""
        if not self._external_client and not self._client.is_closed:
            await self._client.aclose()

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        seed: int | None = None,
    ) -> LLMResponse:
        """Execute chat completion request with exponential backoff on rate limits."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if "googleapis.com" not in self.base_url:
            payload["seed"] = seed if seed is not None else self.default_seed

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        for attempt in range(self.max_retries + 1):
            try:
                response = await self._client.post(url, headers=headers, json=payload)
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < self.max_retries:
                        retry_after = response.headers.get("Retry-After")
                        if retry_after:
                            try:
                                delay = float(retry_after)
                            except ValueError:
                                delay = 2.0 ** attempt + random.uniform(0.1, 0.5)
                        else:
                            delay = 2.0 ** attempt + random.uniform(0.1, 0.5)

                        logger.warning(
                            "llm_rate_limit_or_server_error",
                            status=response.status_code,
                            attempt=attempt,
                            delay=delay,
                        )
                        await asyncio.sleep(delay)
                        continue
                response.raise_for_status()
                data = response.json()
                return self._parse_response(data)
            except httpx.HTTPStatusError as exc:
                if attempt < self.max_retries and exc.response.status_code in (429, 502, 503, 504):
                    delay = 2.0 ** attempt + random.uniform(0.1, 0.5)
                    await asyncio.sleep(delay)
                    continue
                raise
            except httpx.RequestError:
                if attempt < self.max_retries:
                    delay = 2.0 ** attempt + random.uniform(0.1, 0.5)
                    await asyncio.sleep(delay)
                    continue
                raise

        raise RuntimeError(f"Exceeded max retries ({self.max_retries}) contacting LLM API")

    def _parse_response(self, data: dict[str, Any]) -> LLMResponse:
        """Parse OpenAI/Groq response JSON into standardized LLMResponse."""
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content")

        parsed_tool_calls: list[ToolCall] = []
        raw_tool_calls = message.get("tool_calls") or []
        for call in raw_tool_calls:
            call_id = call.get("id", "")
            func = call.get("function", {})
            name = func.get("name", "")
            extra_content = call.get("extra_content")
            args_raw = func.get("arguments", {})
            if isinstance(args_raw, str):
                try:
                    args = json.loads(args_raw)
                except json.JSONDecodeError:
                    args = {"raw": args_raw}
            elif isinstance(args_raw, dict):
                args = args_raw
            else:
                args = {}

            parsed_tool_calls.append(
                ToolCall(
                    id=call_id,
                    name=name,
                    arguments=args,
                    extra_content=extra_content,
                )
            )

        raw_usage = data.get("usage", {})
        prompt_tokens = raw_usage.get("prompt_tokens", 0)
        completion_tokens = raw_usage.get("completion_tokens", 0)
        total_tokens = raw_usage.get("total_tokens", prompt_tokens + completion_tokens)
        usage = Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

        return LLMResponse(
            content=content,
            tool_calls=parsed_tool_calls,
            usage=usage,
            is_final=len(parsed_tool_calls) == 0,
            extra_content=message.get("extra_content"),
        )
