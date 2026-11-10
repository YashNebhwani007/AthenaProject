"""Tool base abstraction, tool decorator, ID generation, and tool registry."""

import asyncio
import functools
import inspect
import time
from collections.abc import Callable
from typing import Any

from athena.logging import get_logger
from athena.schemas import Metric, ToolResult, ToolStatus

logger = get_logger(__name__)


class ToolIDGenerator:
    """Thread-safe sequential tool call ID generator (t1, t2, ...)."""

    def __init__(self, prefix: str = "t") -> None:
        self.prefix = prefix
        self._counter = 0
        self._lock = asyncio.Lock()

    def generate_sync(self) -> str:
        """Generate next ID synchronously."""
        self._counter += 1
        return f"{self.prefix}{self._counter}"

    async def generate(self) -> str:
        """Generate next ID asynchronously."""
        async with self._lock:
            self._counter += 1
            return f"{self.prefix}{self._counter}"

    def reset(self) -> None:
        """Reset sequence counter to 0."""
        self._counter = 0


# Global default ID generator
default_id_generator = ToolIDGenerator()

# Tool registry mapping tool name to its decorated callable
TOOL_REGISTRY: dict[str, Callable[..., Any]] = {}


def register_tool(name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to register a tool function in TOOL_REGISTRY."""

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        tool_name = name or fn.__name__
        TOOL_REGISTRY[tool_name] = fn
        logger.info("tool_registered", name=tool_name)
        return fn

    return decorator


def tool_fn(
    name: str,
    id_generator: ToolIDGenerator | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator wrapping an async or sync analytical tool function.

    Handles:
    - Unique tool execution ID generation (t1, t2...)
    - Execution timing (runtime_ms)
    - Exception handling and error ToolResult formatting
    - Standardized ToolResult wrapping
    """
    id_gen = id_generator or default_id_generator

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        async def async_wrapper(*args: Any, **kwargs: Any) -> ToolResult:
            tool_id = id_gen.generate_sync()
            start_time = time.perf_counter()

            # Record arguments for audit trail
            call_args = {}
            if kwargs:
                call_args.update(kwargs)
            if args:
                call_args["_args"] = [str(a) for a in args]

            try:
                if inspect.iscoroutinefunction(fn):
                    res = await fn(*args, **kwargs)
                else:
                    res = fn(*args, **kwargs)

                duration_ms = (time.perf_counter() - start_time) * 1000.0

                if isinstance(res, ToolResult):
                    # Fill missing fields if not explicitly provided
                    if not res.id:
                        res.id = tool_id
                    if not res.tool:
                        res.tool = name
                    if not res.args:
                        res.args = call_args
                    if res.runtime_ms == 0.0:
                        res.runtime_ms = round(duration_ms, 2)
                    return res

                # If returned tuple of (output, metrics):
                metrics = []
                output = res
                if isinstance(res, tuple) and len(res) == 2 and isinstance(res[1], list):
                    output, metrics = res

                return ToolResult(
                    id=tool_id,
                    tool=name,
                    args=call_args,
                    status=ToolStatus.ok,
                    output=output,
                    metrics=[m if isinstance(m, Metric) else Metric(**m) for m in metrics],
                    runtime_ms=round(duration_ms, 2),
                )
            except Exception as exc:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                logger.error("tool_execution_failed", tool=name, id=tool_id, error=str(exc))
                return ToolResult(
                    id=tool_id,
                    tool=name,
                    args=call_args,
                    status=ToolStatus.error,
                    output=None,
                    warnings=[f"Execution failed in '{name}': {exc}"],
                    runtime_ms=round(duration_ms, 2),
                )

        return async_wrapper

    return decorator
