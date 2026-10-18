"""Athena LLM client package and factory."""

from athena.config import Settings
from athena.config import settings as global_settings
from athena.llm.base import LLMClient, LLMResponse, ToolCall, Usage
from athena.llm.cache import CachedLLMClient
from athena.llm.demo_client import DemoLLMClient
from athena.llm.groq_client import GroqClient


def create_llm_client(app_settings: Settings | None = None) -> LLMClient:
    """Factory creating configured LLM client with optional cache wrapper."""
    cfg = app_settings or global_settings

    if cfg.demo_mode or cfg.llm_provider.lower() == "demo":
        return DemoLLMClient()

    if cfg.llm_provider.lower() == "groq":
        base_client: LLMClient = GroqClient(
            api_key=cfg.llm_api_key,
            model=cfg.llm_model,
            base_url=cfg.llm_base_url,
            max_retries=cfg.llm_max_retries,
            default_seed=cfg.llm_seed,
        )
    else:
        # Defaults to OpenAI-compatible interface (e.g. Ollama, Cerebras)
        base_client = GroqClient(
            api_key=cfg.llm_api_key,
            model=cfg.llm_model,
            base_url=cfg.llm_base_url,
            max_retries=cfg.llm_max_retries,
            default_seed=cfg.llm_seed,
        )

    if cfg.llm_cache_mode.lower() != "off":
        return CachedLLMClient(
            inner_client=base_client,
            provider=cfg.llm_provider,
            model=cfg.llm_model,
            cache_mode=cfg.llm_cache_mode,
        )

    return base_client


__all__ = [
    "CachedLLMClient",
    "DemoLLMClient",
    "GroqClient",
    "LLMClient",
    "LLMResponse",
    "ToolCall",
    "Usage",
    "create_llm_client",
]
