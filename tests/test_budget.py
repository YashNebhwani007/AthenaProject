"""Tests for execution Budget and limit enforcement."""

import time

import pytest

from athena.agent.budget import Budget, BudgetExhausted


def test_budget_within_limits():
    """Verify normal recording increments without raising exceptions."""
    b = Budget(max_steps=5, max_tool_calls=5, max_tokens=1000, timeout_seconds=10.0)
    b.record_step(2)
    b.record_tool_call(3)
    b.record_tokens(500)

    snap = b.to_dict()
    assert snap["steps"] == 2
    assert snap["tool_calls"] == 3
    assert snap["tokens"] == 500
    assert snap["elapsed_seconds"] >= 0.0


def test_budget_exceeds_max_steps():
    """Verify exceeding max_steps raises BudgetExhausted."""
    b = Budget(max_steps=2)
    b.record_step(1)
    b.record_step(1)

    with pytest.raises(BudgetExhausted) as exc_info:
        b.record_step(1)
    assert exc_info.value.limit_name == "max_steps"
    assert exc_info.value.current_value == 3


def test_budget_exceeds_max_tool_calls():
    """Verify exceeding max_tool_calls raises BudgetExhausted."""
    b = Budget(max_tool_calls=2)
    b.record_tool_call(2)

    with pytest.raises(BudgetExhausted) as exc_info:
        b.record_tool_call(1)
    assert exc_info.value.limit_name == "max_tool_calls"
    assert exc_info.value.current_value == 3


def test_budget_exceeds_max_tokens():
    """Verify exceeding max_tokens raises BudgetExhausted."""
    b = Budget(max_tokens=100)
    b.record_tokens(80)

    with pytest.raises(BudgetExhausted) as exc_info:
        b.record_tokens(30)
    assert exc_info.value.limit_name == "max_tokens"
    assert exc_info.value.current_value == 110


def test_budget_exceeds_timeout():
    """Verify timeout expiration raises BudgetExhausted."""
    b = Budget(timeout_seconds=0.01)
    time.sleep(0.02)

    with pytest.raises(BudgetExhausted) as exc_info:
        b.record_step(1)
    assert exc_info.value.limit_name == "timeout_seconds"
