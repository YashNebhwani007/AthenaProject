"""Execution budget tracker enforcing step, tool call, token, and time limits."""

import time
from typing import Any

from athena.config import Settings
from athena.config import settings as global_settings


class BudgetExhausted(Exception):
    """Raised when an execution budget limit has been reached or exceeded."""

    def __init__(
        self,
        reason: str,
        limit_name: str,
        current_value: float,
        limit_value: float,
    ) -> None:
        super().__init__(f"{reason}: {limit_name}={current_value} (limit={limit_value})")
        self.reason = reason
        self.limit_name = limit_name
        self.current_value = current_value
        self.limit_value = limit_value


class Budget:
    """Tracks and enforces execution limits for an analytical agent run."""

    def __init__(
        self,
        max_steps: int | None = None,
        max_tool_calls: int | None = None,
        max_tokens: int | None = None,
        timeout_seconds: float | None = None,
        app_settings: Settings | None = None,
    ) -> None:
        cfg = app_settings or global_settings
        self.max_steps = max_steps if max_steps is not None else cfg.max_steps
        self.max_tool_calls = max_tool_calls if max_tool_calls is not None else cfg.max_tool_calls
        self.max_tokens = max_tokens if max_tokens is not None else cfg.max_tokens
        self.timeout_seconds = (
            timeout_seconds if timeout_seconds is not None else float(cfg.timeout_seconds)
        )

        self.steps: int = 0
        self.tool_calls: int = 0
        self.tokens: int = 0
        self.start_time: float = time.perf_counter()

    @property
    def elapsed_seconds(self) -> float:
        """Return total elapsed wall-clock seconds since budget initialization."""
        return time.perf_counter() - self.start_time

    def check_timeout(self) -> None:
        """Verify elapsed time has not exceeded timeout limit."""
        elapsed = self.elapsed_seconds
        if elapsed > self.timeout_seconds:
            raise BudgetExhausted(
                reason="Execution time limit exceeded",
                limit_name="timeout_seconds",
                current_value=round(elapsed, 2),
                limit_value=self.timeout_seconds,
            )

    def record_step(self, count: int = 1) -> None:
        """Increment step counter and assert within limit."""
        self.check_timeout()
        self.steps += count
        if self.steps > self.max_steps:
            raise BudgetExhausted(
                reason="Maximum orchestration steps exceeded",
                limit_name="max_steps",
                current_value=self.steps,
                limit_value=self.max_steps,
            )

    def record_tool_call(self, count: int = 1) -> None:
        """Increment tool call counter and assert within limit."""
        self.check_timeout()
        self.tool_calls += count
        if self.tool_calls > self.max_tool_calls:
            raise BudgetExhausted(
                reason="Maximum tool calls exceeded",
                limit_name="max_tool_calls",
                current_value=self.tool_calls,
                limit_value=self.max_tool_calls,
            )

    def record_tokens(self, count: int) -> None:
        """Increment token counter and assert within limit."""
        self.check_timeout()
        self.tokens += count
        if self.tokens > self.max_tokens:
            raise BudgetExhausted(
                reason="Maximum token allowance exceeded",
                limit_name="max_tokens",
                current_value=self.tokens,
                limit_value=self.max_tokens,
            )

    def to_dict(self) -> dict[str, Any]:
        """Return current budget usage snapshot."""
        return {
            "steps": self.steps,
            "max_steps": self.max_steps,
            "tool_calls": self.tool_calls,
            "max_tool_calls": self.max_tool_calls,
            "tokens": self.tokens,
            "max_tokens": self.max_tokens,
            "elapsed_seconds": round(self.elapsed_seconds, 2),
            "timeout_seconds": self.timeout_seconds,
        }
