"""Tests for profile_dataset tool."""

from pathlib import Path

import pytest

from athena.data import DatasetRegistry
from athena.schemas import ToolStatus
from athena.tools.profile import profile_dataset


@pytest.fixture
def fixture_path() -> Path:
    return Path(__file__).parent.parent / "fixtures" / "test_data.csv"


@pytest.mark.asyncio
async def test_profile_dataset_expectations(fixture_path: Path):
    """Verify profile_dataset matches hand-verified dataset properties."""
    registry = DatasetRegistry()
    registry.register(dataset_id="fixture_dataset", file_path=fixture_path)

    result = await profile_dataset(dataset_id="fixture_dataset", registry=registry)

    assert result.status == ToolStatus.ok
    assert result.tool == "profile"

    out = result.output
    assert out["row_count"] == 100
    assert out["column_count"] == 6
    assert out["duplicate_rows"] == 1

    # Check metrics
    metric_map = {m.name: m.value for m in result.metrics}
    assert metric_map["row_count"] == 100
    assert metric_map["column_count"] == 6
    assert metric_map["duplicate_rows"] == 1
    assert metric_map["columns_with_high_missingness"] == 1

    # Check heuristics
    assert "churn" in out["suspected_targets"]
    assert "constant_status" in out["constant_columns"]
    assert "notes" in out["high_missingness_columns"]

    # Verify column statistics
    cols = out["columns"]
    monthly = cols["monthly_charges"]
    assert monthly["is_numeric"] is True
    assert monthly["min"] == 15.0
    assert monthly["max"] == 110.0
    assert monthly["mean"] is not None

    cat = cols["category"]
    assert cat["is_numeric"] is False
    assert len(cat["top_categories"]) > 0

    # Verify quality warnings
    warnings_text = " ".join(out["quality_warnings"])
    assert "notes" in warnings_text
    assert "constant_status" in warnings_text

    registry.cleanup()
