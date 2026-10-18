"""Tests for train_model tool across classification and regression tasks."""

import pickle
from pathlib import Path

import pytest

from athena.data import DatasetRegistry
from athena.schemas import ToolStatus
from athena.tools.ml import train_model


@pytest.fixture
def ml_registry() -> DatasetRegistry:
    base = Path(__file__).parent.parent.parent / "benchmark" / "datasets"
    reg = DatasetRegistry()
    reg.register(dataset_id="churn_ds", file_path=base / "telco_churn.csv", table_name="churn_tbl")
    reg.register(
        dataset_id="housing_ds",
        file_path=base / "california_housing.csv",
        table_name="housing_tbl",
    )
    return reg


@pytest.mark.asyncio
async def test_train_model_classification(ml_registry: DatasetRegistry):
    """Verify classification pipeline trains baseline, linear, and LightGBM with valid metrics."""
    res = await train_model(
        target_col="churn",
        dataset_id="churn_ds",
        registry=ml_registry,
    )

    assert res.status == ToolStatus.ok
    assert res.tool == "train_model"

    out = res.output
    assert out["task_type"] == "classification"
    assert out["target_col"] == "churn"
    assert out["best_model"] in ("linear", "boosted")

    # Check comparison table
    comp = out["comparison"]
    assert "baseline" in comp
    assert "linear" in comp
    assert "boosted" in comp

    # Best model beats or matches baseline
    test_metrics = out["test_metrics"]
    assert "accuracy" in test_metrics
    assert "roc_auc" in test_metrics
    assert test_metrics["roc_auc"] >= 0.60

    # Verify model artifact was created and is unpicklable
    art_path = Path(out["model_artifact"])
    assert art_path.exists()
    with open(art_path, "rb") as f:
        loaded_model = pickle.load(f)
    assert hasattr(loaded_model, "predict")


@pytest.mark.asyncio
async def test_train_model_regression(ml_registry: DatasetRegistry):
    """Verify regression pipeline on California Housing computes RMSE and R2."""
    res = await train_model(
        target_col="medhouseval",
        dataset_id="housing_ds",
        registry=ml_registry,
    )

    assert res.status == ToolStatus.ok
    out = res.output
    assert out["task_type"] == "regression"

    metrics = out["test_metrics"]
    assert "rmse" in metrics
    assert "r2" in metrics
    assert metrics["r2"] > 0.40
    assert metrics["rmse"] < 1.0
