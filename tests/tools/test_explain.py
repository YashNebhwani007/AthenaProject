"""Tests for explain_model SHAP tool."""

from pathlib import Path

import pytest

from athena.config import Settings
from athena.data import DatasetRegistry
from athena.schemas import ToolStatus
from athena.tools.explain import explain_model
from athena.tools.ml import train_model


@pytest.mark.asyncio
async def test_explain_model_end_to_end(tmp_path: Path):
    settings = Settings(data_dir=str(tmp_path))
    registry = DatasetRegistry()

    csv_path = Path("tests/fixtures/test_data.csv").resolve()
    registry.register("test_churn", csv_path)

    # 1. Train model first
    train_res = await train_model(
        target_col="churn",
        dataset_id="test_churn",
        registry=registry,
        app_settings=settings,
    )
    assert train_res.status == ToolStatus.ok
    model_id = train_res.output["model_id"]

    # 2. Run explain_model
    explain_res = await explain_model(
        model_id=model_id,
        dataset_id="test_churn",
        target_col="churn",
        sample_index=0,
        registry=registry,
        app_settings=settings,
    )

    assert explain_res.status == ToolStatus.ok
    assert explain_res.output["model_id"] == model_id
    assert len(explain_res.output["global_importance"]) > 0
    assert len(explain_res.output["local_explanation"]) > 0
    assert len(explain_res.artifacts) == 2

    # Check files exist on disk
    for art in explain_res.artifacts:
        p = Path(art.ref)
        assert p.exists()
        assert p.stat().st_size > 0

    # Check metrics
    metric_names = [m.name for m in explain_res.metrics]
    assert "top_feature" in metric_names
    assert "top_feature_importance" in metric_names
