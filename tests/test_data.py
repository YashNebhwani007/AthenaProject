"""Tests for Athena data registry, secure loaders, and DuckDB hardening."""

from pathlib import Path

import duckdb
import pandas as pd
import pytest

from athena.config import Settings
from athena.data import DatasetRegistry


@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    """Create a temporary sample CSV file."""
    csv_file = tmp_path / "customers.csv"
    df = pd.DataFrame(
        {
            "customer_id": [1, 2, 3, 4, 5],
            "churn": [0, 1, 0, 0, 1],
            "monthly_fee": [29.99, 79.50, 49.00, 99.00, 35.50],
            "contract": [
                "month-to-month",
                "one-year",
                "month-to-month",
                "two-year",
                "month-to-month",
            ],
        }
    )
    df.to_csv(csv_file, index=False)
    return csv_file


@pytest.fixture
def sample_parquet(tmp_path: Path) -> Path:
    """Create a temporary sample Parquet file."""
    pq_file = tmp_path / "sales.parquet"
    df = pd.DataFrame(
        {
            "item_id": [101, 102, 103],
            "revenue": [500.0, 1200.5, 300.0],
        }
    )
    df.to_parquet(pq_file, index=False)
    return pq_file


def test_csv_loading_and_querying(sample_csv: Path):
    """Verify CSV loads into registry and queries execute successfully."""
    registry = DatasetRegistry()
    handle = registry.register(dataset_id="test_churn", file_path=sample_csv)

    assert handle.dataset_id == "test_churn"
    assert handle.row_count == 5
    assert handle.column_count == 4
    assert len(handle.columns) == 4

    conn = registry.get_connection("test_churn")
    rows = conn.execute(f"SELECT count(*) FROM {handle.table_name}").fetchone()
    assert rows is not None and rows[0] == 5

    samples = registry.get_sample_rows("test_churn", n=2)
    assert len(samples) == 2
    assert "customer_id" in samples[0]

    summary = registry.get_schema_summary("test_churn")
    assert "customer_id" in summary
    assert "monthly_fee" in summary

    registry.cleanup("test_churn")


def test_parquet_loading(sample_parquet: Path):
    """Verify Parquet loads into registry."""
    registry = DatasetRegistry()
    handle = registry.register(dataset_id="test_sales", file_path=sample_parquet)
    assert handle.row_count == 3
    assert handle.column_count == 2
    registry.cleanup()


def test_duckdb_hardening_blocks_external_access(sample_csv: Path, tmp_path: Path):
    """Verify that file exports/external access are blocked by security hardening."""
    registry = DatasetRegistry()
    handle = registry.register(dataset_id="sec_test", file_path=sample_csv)
    conn = registry.get_connection("sec_test")

    out_file = str(tmp_path / "leak.csv").replace("\\", "/")
    with pytest.raises(duckdb.PermissionException):
        conn.execute(f"COPY {handle.table_name} TO '{out_file}'")

    with pytest.raises(duckdb.PermissionException):
        conn.execute("SELECT * FROM read_csv_auto('http://example.com/data.csv')")

    registry.cleanup()


def test_oversized_file_rejected(tmp_path: Path):
    """Verify file exceeding size limit is rejected with ValueError."""
    fake_file = tmp_path / "huge.csv"
    fake_file.write_text("a,b\n1,2\n" + "x" * 2000, encoding="utf-8")

    # Limit to practically 0 MB (1000 bytes)
    strict_settings = Settings(max_file_size_mb=0, demo_max_file_size_mb=0)
    registry = DatasetRegistry(app_settings=strict_settings)

    with pytest.raises(ValueError, match="exceeds maximum allowed limit"):
        registry.register(dataset_id="oversized", file_path=fake_file)


def test_row_limit_rejected(sample_csv: Path):
    """Verify file exceeding max rows is rejected."""
    strict_settings = Settings(max_rows=2)
    registry = DatasetRegistry(app_settings=strict_settings)

    with pytest.raises(ValueError, match="Row count"):
        registry.register(dataset_id="too_many_rows", file_path=sample_csv)


def test_csv_semicolon_delimited_loading(tmp_path: Path):
    """Verify registry loads CSV files using semicolon delimiters."""
    csv_file = tmp_path / "semicolon.csv"
    csv_file.write_text("col_a;col_b;col_c\n10;20;30\n40;50;60\n", encoding="utf-8")

    registry = DatasetRegistry()
    handle = registry.register(dataset_id="semi_ds", file_path=csv_file)

    assert handle.row_count == 2
    assert handle.column_count == 3
    assert {c.name for c in handle.columns} == {"col_a", "col_b", "col_c"}
    registry.cleanup("semi_ds")
