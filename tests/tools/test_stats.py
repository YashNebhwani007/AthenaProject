"""Tests for statistical test recommendation and hypothesis test execution."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from athena.data import DatasetRegistry
from athena.schemas import ToolStatus
from athena.tools.stats import recommend_test, stats_test


@pytest.fixture
def stats_registry(tmp_path: Path) -> DatasetRegistry:
    """Create fixture dataset with normal and non-normal groups and correlations."""
    np.random.seed(42)
    n = 150

    # Normal distribution
    normal_a = np.random.normal(loc=50, scale=10, size=n)
    normal_b = np.random.normal(loc=60, scale=10, size=n)

    # Correlated numerics
    num_x = np.random.normal(loc=100, scale=15, size=n)
    num_y = 0.8 * num_x + np.random.normal(loc=0, scale=5, size=n)

    # Categories
    group_2 = ["group_1"] * (n // 2) + ["group_2"] * (n // 2)
    group_3 = ["A"] * (n // 3) + ["B"] * (n // 3) + ["C"] * (n // 3)
    cat_binary = np.random.choice(["yes", "no"], size=n)

    df = pd.DataFrame(
        {
            "num_normal": normal_a,
            "num_group_b": normal_b,
            "num_x": num_x,
            "num_y": num_y,
            "group_2": group_2,
            "group_3": group_3,
            "cat_binary": cat_binary,
        }
    )

    file_path = tmp_path / "stats_data.csv"
    df.to_csv(file_path, index=False)

    reg = DatasetRegistry()
    reg.register(dataset_id="stats_ds", file_path=file_path)
    return reg


@pytest.mark.asyncio
async def test_recommend_and_run_two_group_comparison(stats_registry: DatasetRegistry):
    """Verify recommendation and execution for 2-group numeric comparison."""
    rec = await recommend_test(
        dataset_id="stats_ds",
        var1="num_normal",
        var2="group_2",
        registry=stats_registry,
    )
    valid_tests = ("independent_t_test", "welch_t_test", "mann_whitney_u")
    assert rec.output["recommended_test"] in valid_tests

    # Run independent t-test
    res = await stats_test(
        test_name="independent_t_test",
        dataset_id="stats_ds",
        var1="num_normal",
        var2="group_2",
        registry=stats_registry,
    )
    assert res.status == ToolStatus.ok
    out = res.output
    assert "statistic" in out
    assert "p_value" in out
    assert out["effect_size_type"] == "cohens_d"
    assert "confidence_interval" in out


@pytest.mark.asyncio
async def test_recommend_and_run_three_group_comparison(stats_registry: DatasetRegistry):
    """Verify recommendation and execution for 3-group ANOVA / Kruskal-Wallis."""
    rec = await recommend_test(
        dataset_id="stats_ds",
        var1="num_normal",
        var2="group_3",
        registry=stats_registry,
    )
    assert rec.status == ToolStatus.ok
    assert rec.output["recommended_test"] in ("one_way_anova", "kruskal_wallis")

    res = await stats_test(
        test_name="one_way_anova",
        dataset_id="stats_ds",
        var1="num_normal",
        var2="group_3",
        registry=stats_registry,
    )
    assert res.status == ToolStatus.ok
    assert res.output["effect_size_type"] == "eta_squared"
    assert 0.0 <= res.output["effect_size"] <= 1.0


@pytest.mark.asyncio
async def test_recommend_and_run_correlation(stats_registry: DatasetRegistry):
    """Verify correlation test recommendation and execution."""
    rec = await recommend_test(
        dataset_id="stats_ds",
        var1="num_x",
        var2="num_y",
        comparison_type="correlation",
        registry=stats_registry,
    )
    assert rec.status == ToolStatus.ok
    assert rec.output["recommended_test"] in ("pearson", "spearman")

    res = await stats_test(
        test_name="pearson",
        dataset_id="stats_ds",
        var1="num_x",
        var2="num_y",
        registry=stats_registry,
    )
    assert res.status == ToolStatus.ok
    assert res.output["effect_size_type"] == "r"
    assert res.output["effect_size"] > 0.5
    assert res.output["significant"] is True


@pytest.mark.asyncio
async def test_bonferroni_correction(stats_registry: DatasetRegistry):
    """Verify Bonferroni correction divides alpha by n_tests_in_session."""
    res = await stats_test(
        test_name="pearson",
        dataset_id="stats_ds",
        var1="num_x",
        var2="num_y",
        alpha=0.05,
        n_tests_in_session=5,
        registry=stats_registry,
    )
    assert res.status == ToolStatus.ok
    assert res.output["alpha"] == 0.05
    assert res.output["corrected_alpha"] == 0.01


@pytest.mark.asyncio
async def test_stats_test_chi_square_categorical(tmp_path: Path):
    """Verify Chi-square test on 2x2 categorical contingency table."""
    df = pd.DataFrame(
        {
            "gender": ["M"] * 50 + ["F"] * 50,
            "purchased": ["yes"] * 35 + ["no"] * 15 + ["yes"] * 20 + ["no"] * 30,
        }
    )
    file_path = tmp_path / "chi_data.csv"
    df.to_csv(file_path, index=False)
    reg = DatasetRegistry()
    reg.register(dataset_id="chi_ds", file_path=file_path)

    res = await stats_test(
        test_name="chi_square",
        dataset_id="chi_ds",
        var1="gender",
        var2="purchased",
        registry=reg,
    )
    assert res.status == ToolStatus.ok
    assert "p_value" in res.output
    assert res.output["effect_size_type"] == "cramers_v"
    assert 0.0 <= res.output["effect_size"] <= 1.0


@pytest.mark.asyncio
async def test_stats_test_mann_whitney_non_normal(stats_registry: DatasetRegistry):
    """Verify Mann-Whitney U test execution on 2-group comparison."""
    res = await stats_test(
        test_name="mann_whitney_u",
        dataset_id="stats_ds",
        var1="num_normal",
        var2="group_2",
        registry=stats_registry,
    )
    assert res.status == ToolStatus.ok
    assert res.output["test_name"] == "mann_whitney_u"
    assert "p_value" in res.output
    assert res.output["effect_size_type"] == "cohens_d"
