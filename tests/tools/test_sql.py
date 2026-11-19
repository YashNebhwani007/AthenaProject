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


@pytest.mark.asyncio
async def test_run_sql_cte_and_case_expression(dataset_registry: DatasetRegistry):
    """Verify run_sql supports Common Table Expressions (CTEs) and CASE WHEN expressions."""
    query = """
    WITH segmented AS (
        SELECT
            customer_id,
            CASE
                WHEN monthly_charges > 70 THEN 'high'
                ELSE 'low'
            END AS charge_tier
        FROM customers
    )
    SELECT charge_tier, count(*) AS tier_count
    FROM segmented
    GROUP BY charge_tier
    ORDER BY charge_tier
    """
    result = await run_sql(query=query, dataset_id="test_ds", registry=dataset_registry)

    assert result.status == ToolStatus.ok
    assert "charge_tier" in result.output["columns"]
    assert "tier_count" in result.output["columns"]
    assert len(result.output["rows"]) > 0


@pytest.mark.asyncio
async def test_run_sql_window_functions(dataset_registry: DatasetRegistry):
    """Verify run_sql supports window functions with PARTITION BY and OVER."""
    query = """
    SELECT
        customer_id,
        churn,
        monthly_charges,
        AVG(monthly_charges) OVER (PARTITION BY churn) AS avg_churn_charges
    FROM customers
    LIMIT 10
    """
    result = await run_sql(query=query, dataset_id="test_ds", registry=dataset_registry)

    assert result.status == ToolStatus.ok
    assert "avg_churn_charges" in result.output["columns"]
    assert len(result.output["rows"]) == 10


@pytest.mark.asyncio
async def test_run_sql_math_functions(dataset_registry: DatasetRegistry):
    """Verify run_sql supports mathematical functions ROUND, ABS, and SQRT."""
    query = """
    SELECT
        customer_id,
        ROUND(monthly_charges, 1) AS rounded_charges,
        ABS(monthly_charges - 50.0) AS diff_from_50,
        SQRT(monthly_charges) AS sqrt_charges
    FROM customers
    LIMIT 5
    """
    result = await run_sql(query=query, dataset_id="test_ds", registry=dataset_registry)

    assert result.status == ToolStatus.ok
    assert "rounded_charges" in result.output["columns"]
    assert "diff_from_50" in result.output["columns"]
    assert "sqrt_charges" in result.output["columns"]
    assert len(result.output["rows"]) == 5
