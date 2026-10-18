"""Tests for tool base decorator, ID generator, and registry."""

import asyncio

import pytest

from athena.schemas import Metric, ToolResult, ToolStatus
from athena.tools import (
    TOOL_REGISTRY,
    ToolIDGenerator,
    register_tool,
    tool_fn,
)


def test_tool_id_generator():
    """Verify ToolIDGenerator produces sequential prefixed IDs and resets."""
    gen = ToolIDGenerator(prefix="t")
    assert gen.generate_sync() == "t1"
    assert gen.generate_sync() == "t2"
    assert gen.generate_sync() == "t3"

    gen.reset()
    assert gen.generate_sync() == "t1"


@pytest.mark.asyncio
async def test_tool_registration_and_execution():
    """Verify tool registers in TOOL_REGISTRY and returns valid ToolResult."""
    id_gen = ToolIDGenerator(prefix="t")

    @register_tool("calculator")
    @tool_fn("calculator", id_generator=id_gen)
    async def add_numbers(a: int, b: int) -> int:
        await asyncio.sleep(0.01)
        return a + b

    assert "calculator" in TOOL_REGISTRY
    assert TOOL_REGISTRY["calculator"] is add_numbers

    result = await add_numbers(a=10, b=32)

    assert isinstance(result, ToolResult)
    assert result.id == "t1"
    assert result.tool == "calculator"
    assert result.status == ToolStatus.ok
    assert result.output == 42
    assert result.args == {"a": 10, "b": 32}
    assert result.runtime_ms >= 5.0
    assert result.warnings == []


@pytest.mark.asyncio
async def test_tool_error_handling():
    """Verify tool exceptions are caught and wrapped into an error ToolResult."""
    id_gen = ToolIDGenerator(prefix="err_")

    @tool_fn("failing_tool", id_generator=id_gen)
    async def crash_tool():
        raise ZeroDivisionError("division by zero in statistical test")

    result = await crash_tool()

    assert isinstance(result, ToolResult)
    assert result.id == "err_1"
    assert result.tool == "failing_tool"
    assert result.status == ToolStatus.error
    assert result.output is None
    assert len(result.warnings) == 1
    assert "division by zero" in result.warnings[0]
    assert result.runtime_ms >= 0.0


@pytest.mark.asyncio
async def test_tool_returning_explicit_tool_result():
    """Verify tools returning ToolResult instances preserve their metrics and artifacts."""
    id_gen = ToolIDGenerator(prefix="t")

    @tool_fn("custom_tool", id_generator=id_gen)
    def make_metrics():
        return ToolResult(
            id="",
            tool="",
            output={"status": "complete"},
            metrics=[Metric(name="accuracy", value=0.95)],
        )

    result = await make_metrics()

    assert result.id == "t1"
    assert result.tool == "custom_tool"
    assert result.status == ToolStatus.ok
    assert result.metrics[0].name == "accuracy"
    assert result.metrics[0].value == 0.95
