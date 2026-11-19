"""Tests for train_model tool across classification and regression tasks."""

import pickle
from pathlib import Path

import pandas as pd
import pytest

from athena.data import DatasetRegistry
from athena.schemas import ToolStatus
from athena.tools.ml import predict_model, train_model


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


@pytest.mark.asyncio
async def test_predict_model_classification(ml_registry: DatasetRegistry):
    """Verify predict_model produces prediction and probability for classification sample."""
    train_res = await train_model(
        target_col="churn",
        dataset_id="churn_ds",
        registry=ml_registry,
    )
    model_id = train_res.output["model_id"]

    sample_features = {
        "tenure": 2,
        "monthly_charges": 85.5,
        "contract": "Month-to-month",
        "tech_support": "No",
    }
    pred_res = await predict_model(
        features=sample_features,
        model_id=model_id,
        dataset_id="churn_ds",
        registry=ml_registry,
    )

    assert pred_res.status == ToolStatus.ok
    assert pred_res.tool == "predict_model"
    assert "prediction" in pred_res.output
    assert pred_res.output["prediction"] in (0, 1)
    assert pred_res.output["probability"] is not None
    assert 0.0 <= pred_res.output["probability"] <= 1.0
    assert any(m.name == "probability_percent" for m in pred_res.metrics)


@pytest.mark.asyncio
async def test_predict_model_auto_train(ml_registry: DatasetRegistry):
    """Verify predict_model auto-trains model if model_id is omitted."""
    sample_features = {
        "tenure": 60,
        "monthly_charges": 20.0,
        "contract": "Two year",
    }
    pred_res = await predict_model(
        features=sample_features,
        target_col="churn",
        dataset_id="churn_ds",
        registry=ml_registry,
    )

    assert pred_res.status == ToolStatus.ok
    assert "prediction" in pred_res.output
    assert pred_res.output["prediction"] in (0, 1)


@pytest.mark.asyncio
async def test_train_model_reproducibility_with_seed(ml_registry: DatasetRegistry):
    """Verify train_model produces identical metrics when passing fixed random seed."""
    from athena.config import Settings

    cfg1 = Settings(random_seed=42)
    cfg2 = Settings(random_seed=42)

    res1 = await train_model(
        target_col="churn",
        dataset_id="churn_ds",
        registry=ml_registry,
        app_settings=cfg1,
    )
    res2 = await train_model(
        target_col="churn",
        dataset_id="churn_ds",
        registry=ml_registry,
        app_settings=cfg2,
    )

    assert res1.status == ToolStatus.ok
    assert res2.status == ToolStatus.ok
    assert res1.output["test_metrics"]["roc_auc"] == res2.output["test_metrics"]["roc_auc"]


@pytest.mark.asyncio
async def test_train_model_with_zero_variance_feature(tmp_path: Path):
    """Verify classification pipeline trains when a zero-variance feature is present."""
    df = pd.DataFrame(
        {
            "const_feat": [1.0] * 80,
            "var_feat": [float(i) for i in range(80)],
            "label": [0] * 40 + [1] * 40,
        }
    )
    file_path = tmp_path / "zero_var_data.csv"
    df.to_csv(file_path, index=False)

    reg = DatasetRegistry()
    reg.register(dataset_id="zero_var_ds", file_path=file_path)

    res = await train_model(
        target_col="label",
        dataset_id="zero_var_ds",
        registry=reg,
    )
    assert res.status == ToolStatus.ok
    assert "accuracy" in res.output["test_metrics"]
