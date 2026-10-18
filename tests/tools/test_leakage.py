"""Tests for data leakage detection tool."""

from pathlib import Path

import pytest

from athena.data import DatasetRegistry
from athena.schemas import ToolStatus
from athena.tools.leakage import check_leakage


@pytest.fixture
def leakage_registry() -> DatasetRegistry:
    base = Path(__file__).parent.parent / "fixtures"
    bench_base = Path(__file__).parent.parent.parent / "benchmark" / "datasets"

    reg = DatasetRegistry()
    reg.register(
        dataset_id="leaky_ds",
        file_path=base / "test_data_leaky.csv",
        table_name="leaky_tbl",
    )
    reg.register(
        dataset_id="clean_housing",
        file_path=bench_base / "california_housing.csv",
        table_name="clean_housing_tbl",
    )
    return reg


@pytest.mark.asyncio
async def test_detects_planted_leakage(leakage_registry: DatasetRegistry):
    """Verify tool catches planted target leakage and suspicious names with high severity."""
    res = await check_leakage(
        target_col="churn",
        dataset_id="leaky_ds",
        registry=leakage_registry,
    )

    assert res.status == ToolStatus.ok
    assert res.tool == "check_leakage"

    out = res.output
    assert out["has_leakage"] is True
    assert out["max_severity"] == "high"

    # Confirms cancellation_fee was identified
    assert "cancellation_fee" in out["suspicious_columns"]

    check_types = {f["check_name"] for f in out["findings"] if f["severity"] == "high"}
    assert "suspicious_names" in check_types
    assert "single_feature_auc" in check_types

    metric_map = {m.name: m.value for m in res.metrics}
    assert metric_map["leakage_detected"] == 1
    assert metric_map["high_severity_leak_count"] >= 1


@pytest.mark.asyncio
async def test_no_false_positives_on_clean_data(leakage_registry: DatasetRegistry):
    """Verify clean dataset triggers zero high-severity leakage alarms."""
    res = await check_leakage(
        target_col="medhouseval",
        dataset_id="clean_housing",
        registry=leakage_registry,
    )

    assert res.status == ToolStatus.ok
    out = res.output
    assert out["max_severity"] != "high"

    metric_map = {m.name: m.value for m in res.metrics}
    assert metric_map["high_severity_leak_count"] == 0
