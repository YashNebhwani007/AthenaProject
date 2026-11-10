"""LLM client abstractions and response schemas."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class Usage(BaseModel):
    """Token usage counters for an LLM invocation."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def model_post_init(self, __context: Any) -> None:
        if self.total_tokens == 0 and (self.prompt_tokens or self.completion_tokens):
            self.total_tokens = self.prompt_tokens + self.completion_tokens


class ToolCall(BaseModel):
    """Model-generated tool call request."""

    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    extra_content: dict[str, Any] | None = None


class LLMResponse(BaseModel):
    """Standardized response from any LLM provider."""

    content: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    usage: Usage = Field(default_factory=Usage)
    is_final: bool = False
    extra_content: dict[str, Any] | None = None

    def model_post_init(self, __context: Any) -> None:
        # If is_final is not explicitly set, determine it by absence of tool calls
        if not self.tool_calls and not self.is_final:
            self.is_final = True


class LLMClient(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        seed: int | None = None,
    ) -> LLMResponse:
        """Send chat messages and optional tools to the LLM."""
        ...

    async def close(self) -> None:
        """Release underlying HTTP client resources."""
        pass
