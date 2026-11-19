"""Unit tests for Athena Command Line Interface (CLI)."""

from pathlib import Path

import pytest

from athena.cli import create_parser, run_profile, run_query


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


def test_cli_parser_query_args():
    """Verify CLI parser parses query arguments correctly."""
    parser = create_parser()
    args = parser.parse_args(["query", "data.csv", "--sql", "SELECT 1", "--limit", "10"])
    assert args.command == "query"
    assert args.file == "data.csv"
    assert args.sql == "SELECT 1"
    assert args.limit == 10


@pytest.mark.asyncio
async def test_run_query_execution(capsys):
    """Verify run_query executes valid SQL against dataset file and formats rows."""
    fixture_path = Path("tests/fixtures/test_data.csv").resolve()
    query = "SELECT customer_id, monthly_charges FROM data LIMIT 3"
    code = await run_query(str(fixture_path), sql=query, limit=3)
    assert code == 0

    captured = capsys.readouterr()
    assert "customer_id\tmonthly_charges" in captured.out
    assert "rows returned" in captured.out
