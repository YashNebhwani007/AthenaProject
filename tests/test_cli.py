"""Unit tests for Athena Command Line Interface (CLI)."""

from pathlib import Path

import pytest

from athena.cli import create_parser, run_profile


def test_cli_parser_profile_args():
    """Verify CLI parser parses profile arguments correctly."""
    parser = create_parser()
    args = parser.parse_args(["profile", "data.csv", "--json"])
    assert args.command == "profile"
    assert args.file == "data.csv"
    assert args.json is True


@pytest.mark.asyncio
async def test_run_profile_summary(capsys):
    """Verify run_profile outputs formatted summary text for valid dataset."""
    fixture_path = Path("tests/fixtures/test_data.csv").resolve()
    code = await run_profile(str(fixture_path), as_json=False)
    assert code == 0

    captured = capsys.readouterr()
    assert "Dataset: test_data.csv" in captured.out
    assert "Shape:" in captured.out
    assert "Columns:" in captured.out


@pytest.mark.asyncio
async def test_run_profile_json(capsys):
    """Verify run_profile outputs valid JSON when --json is passed."""
    fixture_path = Path("tests/fixtures/test_data.csv").resolve()
    code = await run_profile(str(fixture_path), as_json=True)
    assert code == 0

    captured = capsys.readouterr()
    assert '"columns":' in captured.out
    assert '"row_count":' in captured.out
