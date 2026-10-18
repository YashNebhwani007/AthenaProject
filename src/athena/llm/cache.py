"""Record and replay caching wrapper for LLM calls."""

import hashlib
import json
from pathlib import Path
from typing import Any

from athena.llm.base import LLMClient, LLMResponse
from athena.logging import get_logger

logger = get_logger(__name__)


class CachedLLMClient(LLMClient):
    """Wrapper that records and replays LLM responses based on request hash."""

    def __init__(
        self,
        inner_client: LLMClient,
        provider: str = "groq",
        model: str = "llama-3.3-70b-versatile",
        cache_mode: str = "auto",
        cache_dir: str | Path | None = None,
    ) -> None:
        self.inner_client = inner_client
        self.provider = provider
        self.model = model
        self.cache_mode = cache_mode.lower()

        clean_model = model.replace("/", "_").replace(":", "_")
        self.cache_dir = Path(cache_dir or f"benchmark/cache/{provider}_{clean_model}")
        if self.cache_mode in ("record", "auto", "replay"):
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _compute_hash(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        seed: int | None,
    ) -> str:
        """Compute deterministic SHA256 hash of model, messages, tools, and seed."""
        key_data = {
            "model": self.model,
            "messages": messages,
            "tools": tools or [],
            "seed": seed,
        }
        serialized = json.dumps(key_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        seed: int | None = None,
    ) -> LLMResponse:
        """Execute chat completion with caching according to configured mode."""
        if self.cache_mode == "off":
            return await self.inner_client.chat(messages=messages, tools=tools, seed=seed)

        req_hash = self._compute_hash(messages, tools, seed)
        cache_path = self.cache_dir / f"{req_hash}.json"

        # Replay mode or Auto mode cache hit
        if self.cache_mode in ("replay", "auto") and cache_path.exists():
            logger.info("llm_cache_hit", hash=req_hash, mode=self.cache_mode)
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            return LLMResponse.model_validate(data["response"])

        if self.cache_mode == "replay":
            raise FileNotFoundError(
                f"LLM cache miss in replay mode for hash {req_hash} at {cache_path}"
            )

        # Record mode or Auto mode cache miss
        logger.info("llm_cache_miss_fetching", hash=req_hash, mode=self.cache_mode)
        response = await self.inner_client.chat(messages=messages, tools=tools, seed=seed)

        cache_data = {
            "hash": req_hash,
            "model": self.model,
            "messages": messages,
            "tools": tools or [],
            "seed": seed,
            "response": response.model_dump(),
        }
        cache_path.write_text(json.dumps(cache_data, indent=2), encoding="utf-8")
        return response

    async def close(self) -> None:
        """Close wrapped client."""
        await self.inner_client.close()
