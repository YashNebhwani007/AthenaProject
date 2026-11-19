"""Tests for structured logging."""

import json

import pytest

from athena.logging import get_logger


def test_structured_logging_json_output(capsys: pytest.CaptureFixture[str]):
    """Verify get_logger outputs valid JSON to stderr with bound keys."""
    logger = get_logger("test_module")
    logger.info("test_event", key="val", count=42)

    captured = capsys.readouterr()
    stderr_output = captured.err.strip()
    assert stderr_output, "Expected output on stderr"

    lines = [line.strip() for line in stderr_output.splitlines() if line.strip()]
    matched = None
    for line in reversed(lines):
        try:
            data = json.loads(line)
            if data.get("event") == "test_event":
                matched = data
                break
        except json.JSONDecodeError:
            continue

    assert matched is not None, f"Could not find valid JSON log in: {stderr_output}"
    assert matched["key"] == "val"
    assert matched["count"] == 42
    assert matched["level"] == "info"
    assert "timestamp" in matched


def test_structured_logging_warning_and_error(capsys: pytest.CaptureFixture[str]):
    """Verify warning and error events contain level and custom metadata."""
    logger = get_logger("error_module")
    logger.warning("warning_event", issue="suboptimal_alpha")
    logger.error("error_event", status_code=500, detail="Database failure")

    captured = capsys.readouterr()
    lines = [
        json.loads(line)
        for line in captured.err.splitlines()
        if line.strip() and line.strip().startswith("{")
    ]
    events = {entry["event"]: entry for entry in lines}

    assert "warning_event" in events
    assert events["warning_event"]["level"] == "warning"
    assert events["warning_event"]["issue"] == "suboptimal_alpha"

    assert "error_event" in events
    assert events["error_event"]["level"] == "error"
    assert events["error_event"]["status_code"] == 500
