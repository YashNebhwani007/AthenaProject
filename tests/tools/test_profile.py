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


@pytest.mark.asyncio
async def test_profile_dataset_single_row(tmp_path: Path):
    """Verify profiling a dataset with exactly one row executes cleanly without errors."""
    import pandas as pd

    df = pd.DataFrame({"id": [1], "feature": [42.0], "label": [0]})
    file_path = tmp_path / "single_row.csv"
    df.to_csv(file_path, index=False)

    reg = DatasetRegistry()
    reg.register(dataset_id="single_row_ds", file_path=file_path)

    res = await profile_dataset(dataset_id="single_row_ds", registry=reg)
    assert res.status == ToolStatus.ok
    assert res.output["row_count"] == 1
    assert res.output["column_count"] == 3
    assert res.output["duplicate_rows"] == 0
    reg.cleanup()


@pytest.mark.asyncio
async def test_profile_dataset_all_null_column(tmp_path: Path):
    """Verify profiling a dataset with a 100% null column identifies high missingness."""
    import pandas as pd

    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "all_null": [None, None, None],
            "valid_feature": [10.0, 20.0, 30.0],
        }
    )
    file_path = tmp_path / "null_col.csv"
    df.to_csv(file_path, index=False)

    reg = DatasetRegistry()
    reg.register(dataset_id="null_col_ds", file_path=file_path)

    res = await profile_dataset(dataset_id="null_col_ds", registry=reg)
    assert res.status == ToolStatus.ok
    assert "all_null" in res.output["high_missingness_columns"]
    assert res.output["columns"]["all_null"]["null_pct"] == 1.0
    reg.cleanup()
