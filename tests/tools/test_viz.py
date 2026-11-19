"""Tests for make_plot visualization tool."""

from pathlib import Path

import pytest

from athena.config import Settings
from athena.data import DatasetRegistry
from athena.schemas import ToolStatus
from athena.tools.viz import make_plot


@pytest.fixture
def dataset_setup(tmp_path: Path):
    settings = Settings(data_dir=str(tmp_path))
    registry = DatasetRegistry()
    csv_path = Path("tests/fixtures/test_data.csv").resolve()
    registry.register("test_ds", csv_path)
    return settings, registry


@pytest.mark.asyncio
async def test_make_plot_histogram(dataset_setup):
    settings, registry = dataset_setup
    res = await make_plot(
        dataset_id="test_ds",
        chart_type="histogram",
        x="monthly_charges",
        registry=registry,
        app_settings=settings,
    )
    assert res.status == ToolStatus.ok
    assert Path(res.output["png_path"]).exists()
    assert Path(res.output["png_path"]).stat().st_size > 0
    assert "monthly_charges" in res.output["text_summary"]
    assert "data" in res.output["plotly_spec"]


@pytest.mark.asyncio
async def test_make_plot_bar(dataset_setup):
    settings, registry = dataset_setup
    res = await make_plot(
        dataset_id="test_ds",
        chart_type="bar",
        x="category",
        y="monthly_charges",
        registry=registry,
        app_settings=settings,
    )
    assert res.status == ToolStatus.ok
    assert Path(res.output["png_path"]).exists()
    assert len(res.metrics) >= 1


@pytest.mark.asyncio
async def test_make_plot_box(dataset_setup):
    settings, registry = dataset_setup
    res = await make_plot(
        dataset_id="test_ds",
        chart_type="box",
        x="category",
        y="monthly_charges",
        registry=registry,
        app_settings=settings,
    )
    assert res.status == ToolStatus.ok
    assert Path(res.output["png_path"]).exists()


@pytest.mark.asyncio
async def test_make_plot_scatter(dataset_setup):
    settings, registry = dataset_setup
    res = await make_plot(
        dataset_id="test_ds",
        chart_type="scatter",
        x="customer_id",
        y="monthly_charges",
        registry=registry,
        app_settings=settings,
    )
    assert res.status == ToolStatus.ok
    assert Path(res.output["png_path"]).exists()
    metric_names = [m.name for m in res.metrics]
    assert "pearson_r" in metric_names


@pytest.mark.asyncio
async def test_make_plot_correlation_heatmap(dataset_setup):
    settings, registry = dataset_setup
    res = await make_plot(
        dataset_id="test_ds",
        chart_type="correlation_heatmap",
        registry=registry,
        app_settings=settings,
    )
    assert res.status == ToolStatus.ok
    assert Path(res.output["png_path"]).exists()
    assert "Heatmap" in str(res.output["plotly_spec"])


@pytest.mark.asyncio
async def test_make_plot_shap_summary(dataset_setup):
    settings, registry = dataset_setup
    res = await make_plot(
        dataset_id="test_ds",
        chart_type="shap_summary",
        registry=registry,
        app_settings=settings,
    )
    assert res.status == ToolStatus.ok
    assert Path(res.output["png_path"]).exists()
    assert len(res.output["text_summary"]) > 0


@pytest.mark.asyncio
async def test_make_plot_unsupported_chart_type_returns_error(dataset_setup):
    """Verify requesting an invalid chart type returns an error tool result."""
    settings, registry = dataset_setup
    res = await make_plot(
        dataset_id="test_ds",
        chart_type="invalid_type",
        registry=registry,
        app_settings=settings,
    )
    assert res.status == ToolStatus.error
    assert len(res.warnings) > 0
    assert "unsupported chart_type" in res.warnings[0].lower()


@pytest.mark.asyncio
async def test_make_plot_histogram_custom_title(dataset_setup):
    """Verify histogram honors custom title formatting."""
    settings, registry = dataset_setup
    res = await make_plot(
        dataset_id="test_ds",
        chart_type="histogram",
        x="monthly_charges",
        title="Custom Charges Distribution",
        registry=registry,
        app_settings=settings,
    )
    assert res.status == ToolStatus.ok
    assert Path(res.output["png_path"]).exists()
    assert res.output["title"] == "Custom Charges Distribution"


@pytest.mark.asyncio
async def test_make_plot_box_multi_group(tmp_path: Path):
    """Verify box plot renders across 3 distinct categorical groups."""
    import pandas as pd

    df = pd.DataFrame({
        "cohort": ["alpha", "beta", "gamma"] * 20,
        "score": [10.0, 20.0, 30.0] * 20,
    })
    csv_file = tmp_path / "multi_box.csv"
    df.to_csv(csv_file, index=False)

    settings = Settings(data_dir=str(tmp_path))
    registry = DatasetRegistry()
    registry.register("multi_box_ds", csv_file)

    res = await make_plot(
        dataset_id="multi_box_ds",
        chart_type="box",
        x="cohort",
        y="score",
        registry=registry,
        app_settings=settings,
    )
    assert res.status == ToolStatus.ok
    assert Path(res.output["png_path"]).exists()
    assert "score" in res.output["text_summary"]
