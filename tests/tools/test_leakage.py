"""Tests for data leakage detection tool."""

from pathlib import Path

import pandas as pd
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


@pytest.mark.asyncio
async def test_leakage_id_column_medium_severity(tmp_path: Path):
    """Verify unique identifier columns are flagged with medium severity memorization risk."""
    df = pd.DataFrame(
        {
            "user_uuid": [f"u_{i:04d}" for i in range(100)],
            "feature_val": [i * 2.5 for i in range(100)],
            "label": [i % 2 for i in range(100)],
        }
    )
    file_path = tmp_path / "id_leak_data.csv"
    df.to_csv(file_path, index=False)

    reg = DatasetRegistry()
    reg.register(dataset_id="id_leak_ds", file_path=file_path)

    res = await check_leakage(
        target_col="label",
        dataset_id="id_leak_ds",
        registry=reg,
    )

    assert res.status == ToolStatus.ok
    out = res.output
    id_findings = [f for f in out["findings"] if f["check_name"] == "id_columns"]
    assert len(id_findings) > 0
    assert id_findings[0]["column"] == "user_uuid"
    assert id_findings[0]["severity"] == "medium"


@pytest.mark.asyncio
async def test_leakage_temporal_column_low_severity(tmp_path: Path):
    """Verify temporal column detection produces low-severity advisory finding."""
    df = pd.DataFrame(
        {
            "event_date": ["2026-01-01", "2026-01-02", "2026-01-03"] * 20,
            "feature": [i * 1.5 for i in range(60)],
            "target": [i % 2 for i in range(60)],
        }
    )
    file_path = tmp_path / "temporal_data.csv"
    df.to_csv(file_path, index=False)

    reg = DatasetRegistry()
    reg.register(dataset_id="temporal_ds", file_path=file_path)

    res = await check_leakage(
        target_col="target",
        dataset_id="temporal_ds",
        registry=reg,
    )

    assert res.status == ToolStatus.ok
    findings = [f for f in res.output["findings"] if f["check_name"] == "temporal_split"]
    assert len(findings) == 1
    assert findings[0]["severity"] == "low"
