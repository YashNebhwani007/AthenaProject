"""Tests for run_sql tool."""

from pathlib import Path

import pytest

from athena.config import Settings
from athena.data import DatasetRegistry
from athena.schemas import ToolStatus
from athena.tools.sql import run_sql


@pytest.fixture
def dataset_registry() -> DatasetRegistry:
    fixture_path = Path(__file__).parent.parent / "fixtures" / "test_data.csv"
    reg = DatasetRegistry()
    reg.register(dataset_id="test_ds", file_path=fixture_path, table_name="customers")
    return reg


@pytest.mark.asyncio
async def test_run_sql_basic_select(dataset_registry: DatasetRegistry):
    """Verify run_sql executes SELECT query and extracts metrics and output."""
    query = "SELECT customer_id, churn, monthly_charges FROM customers WHERE churn = 1"
    result = await run_sql(query=query, dataset_id="test_ds", registry=dataset_registry)

    assert result.status == ToolStatus.ok
    assert result.tool == "run_sql"

    out = result.output
    assert "columns" in out
    assert "rows" in out
    assert out["columns"] == ["customer_id", "churn", "monthly_charges"]
    assert out["total_rows"] > 0
    assert out["truncated"] is False

    metrics = {m.name: m.value for m in result.metrics}
    assert metrics["total_rows"] == out["total_rows"]
    assert metrics["columns_returned"] == 3


@pytest.mark.asyncio
async def test_run_sql_injects_limit(dataset_registry: DatasetRegistry):
    """Verify LIMIT clause is automatically injected when omitted in user query."""
    query = "SELECT * FROM customers"
    result = await run_sql(
        query=query,
        dataset_id="test_ds",
        max_rows=10,
        registry=dataset_registry,
    )

    assert result.status == ToolStatus.ok
    out = result.output
    assert "LIMIT 10" in out["query"].upper()
    assert out["total_rows"] == 10
    assert out["truncated"] is True


@pytest.mark.asyncio
async def test_run_sql_caps_limit_at_setting(dataset_registry: DatasetRegistry):
    """Verify user LIMIT is capped when exceeding max row limit."""
    cfg = Settings(sql_row_limit=5)
    query = "SELECT * FROM customers LIMIT 50"
    result = await run_sql(
        query=query,
        dataset_id="test_ds",
        registry=dataset_registry,
        app_settings=cfg,
    )

    assert result.status == ToolStatus.ok
    out = result.output
    assert out["total_rows"] == 5
    assert out["truncated"] is True


@pytest.mark.asyncio
async def test_run_sql_rejects_malicious_query(dataset_registry: DatasetRegistry):
    """Verify destructive SQL is rejected by validator and returns error ToolResult."""
    attack = "DROP TABLE customers"
    result = await run_sql(query=attack, dataset_id="test_ds", registry=dataset_registry)

    assert result.status == ToolStatus.error
    assert len(result.warnings) > 0
    assert "rejected" in result.warnings[0].lower() or "disallowed" in result.warnings[0].lower()
