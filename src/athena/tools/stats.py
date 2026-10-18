"""Statistical test recommendation and execution tools per ADR-06."""

import math
from typing import Any

import numpy as np
import pandas as pd
import scipy.stats as stats

from athena.data import DatasetRegistry, default_registry
from athena.logging import get_logger
from athena.schemas import Metric, ToolResult, ToolStatus
from athena.tools.base import register_tool, tool_fn

logger = get_logger(__name__)


def _check_normality(data: np.ndarray, alpha: float = 0.05) -> tuple[bool, float]:
    """Test normality with Shapiro-Wilk (n < 5000) or D'Agostino-Pearson (n >= 5000)."""
    clean = data[~np.isnan(data)]
    n = len(clean)
    if n < 3:
        return False, 0.0
    if n < 5000:
        stat, p = stats.shapiro(clean)
    else:
        stat, p = stats.normaltest(clean)
    return bool(p > alpha), float(p)


def _check_equal_variance(groups: list[np.ndarray], alpha: float = 0.05) -> tuple[bool, float]:
    """Test equal variance across groups using Levene's test."""
    clean_groups = [g[~np.isnan(g)] for g in groups if len(g[~np.isnan(g)]) > 1]
    if len(clean_groups) < 2:
        return False, 0.0
    stat, p = stats.levene(*clean_groups)
    return bool(p > alpha), float(p)


def _cohens_d(g1: np.ndarray, g2: np.ndarray) -> float:
    """Calculate Cohen's d effect size for two independent samples."""
    n1, n2 = len(g1), len(g2)
    v1, v2 = np.var(g1, ddof=1), np.var(g2, ddof=1)
    if n1 + n2 <= 2:
        return 0.0
    s_pooled = math.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))
    if s_pooled == 0:
        return 0.0
    return float((np.mean(g1) - np.mean(g2)) / s_pooled)


def _eta_squared(groups: list[np.ndarray]) -> float:
    """Calculate Eta-squared effect size for ANOVA / group comparisons."""
    all_vals = np.concatenate(groups)
    if len(all_vals) == 0:
        return 0.0
    grand_mean = np.mean(all_vals)
    ss_total = np.sum((all_vals - grand_mean) ** 2)
    ss_between = sum(len(g) * (np.mean(g) - grand_mean) ** 2 for g in groups)
    return float(ss_between / ss_total) if ss_total > 0 else 0.0


def _cramers_v(contingency_table: np.ndarray) -> float:
    """Calculate Cramér's V effect size for categorical contingency tables."""
    chi2 = stats.chi2_contingency(contingency_table)[0]
    n = contingency_table.sum()
    r, c = contingency_table.shape
    min_dim = min(r - 1, c - 1)
    if n == 0 or min_dim == 0:
        return 0.0
    return float(math.sqrt((chi2 / n) / min_dim))


@register_tool("recommend_test")
@tool_fn("recommend_test")
async def recommend_test(
    dataset_id: str,
    var1: str,
    var2: str,
    comparison_type: str | None = None,
    alpha: float = 0.05,
    registry: DatasetRegistry | None = None,
) -> ToolResult:
    """Deterministically recommend the statistically appropriate test based on data properties."""
    reg = registry or default_registry
    conn = reg.get_connection(dataset_id)
    handle = reg.get(dataset_id)
    tbl = handle.table_name

    # Load dataframe for the two variables
    df = conn.execute(f'SELECT "{var1}", "{var2}" FROM {tbl}').fetchdf()
    df = df.dropna()

    is_num1 = pd.api.types.is_numeric_dtype(df[var1])
    is_num2 = pd.api.types.is_numeric_dtype(df[var2])

    warnings: list[str] = []
    assumptions: dict[str, Any] = {}

    # Case A: Correlation between two numeric variables
    is_corr = comparison_type == "correlation" or (
        df[var1].nunique() > 10 and df[var2].nunique() > 10
    )
    if is_num1 and is_num2 and is_corr:
        norm1, p1 = _check_normality(df[var1].to_numpy(), alpha)
        norm2, p2 = _check_normality(df[var2].to_numpy(), alpha)
        assumptions["normality"] = {f"{var1}_p": p1, f"{var2}_p": p2}

        if norm1 and norm2:
            test_name = "pearson"
            reason = "Both variables satisfy normality assumptions for linear correlation."
        else:
            test_name = "spearman"
            reason = (
                "At least one variable deviates from normal distribution; "
                "rank correlation recommended."
            )

    # Case B: Comparison of groups (numeric vs categorical)
    elif (
        (is_num1 and not is_num2)
        or (is_num2 and not is_num1)
        or (is_num1 and df[var2].nunique() <= 10)
    ):
        num_col = var1 if is_num1 else var2
        cat_col = var2 if is_num1 else var1

        groups = [group[num_col].to_numpy() for _, group in df.groupby(cat_col)]
        n_groups = len(groups)
        assumptions["n_groups"] = n_groups

        for i, g in enumerate(groups):
            if len(g) < 20:
                warnings.append(f"Group {i} has small sample size ({len(g)} < 20).")

        # Normality and equal variance
        all_normal = True
        normality_pvals = {}
        for idx, g in enumerate(groups):
            is_norm, p_val = _check_normality(g, alpha)
            normality_pvals[f"group_{idx}"] = p_val
            if not is_norm:
                all_normal = False
        assumptions["normality_p"] = normality_pvals

        eq_var, lev_p = _check_equal_variance(groups, alpha)
        assumptions["equal_variance"] = eq_var
        assumptions["levene_p"] = lev_p

        if n_groups == 2:
            if all_normal and eq_var:
                test_name = "independent_t_test"
                reason = "Two groups, normally distributed with equal variances."
            elif all_normal and not eq_var:
                test_name = "welch_t_test"
                reason = (
                    "Two groups, normally distributed but unequal variances "
                    "(Welch's correction needed)."
                )
            else:
                test_name = "mann_whitney_u"
                reason = (
                    "Two groups, non-normal distribution; "
                    "non-parametric Mann-Whitney U test required."
                )
        elif n_groups >= 3:
            if all_normal and eq_var:
                test_name = "one_way_anova"
                reason = f"{n_groups} groups satisfying normality and homogeneity of variance."
            else:
                test_name = "kruskal_wallis"
                reason = f"{n_groups} groups with non-normal distribution or unequal variance."
        else:
            test_name = "invalid"
            reason = "Fewer than 2 distinct groups found in grouping column."
            warnings.append("Grouping variable must have at least 2 categories.")

    # Case C: Association between two categorical variables
    else:
        c_table = pd.crosstab(df[var1], df[var2]).to_numpy()
        chi2_res = stats.chi2_contingency(c_table)
        expected = chi2_res[3]
        min_expected = float(expected.min())
        assumptions["min_expected_cell_count"] = min_expected

        if min_expected < 5:
            if c_table.shape == (2, 2):
                test_name = "fisher_exact"
                reason = (
                    "2x2 contingency table with expected cell counts < 5; "
                    "Fisher's exact test required."
                )
            else:
                test_name = "chi_square"
                reason = (
                    "Chi-square test of independence (note warning on low expected cell counts)."
                )
                warnings.append(
                    "Expected cell counts < 5 in contingency table "
                    "may reduce Chi-square reliability."
                )
        else:
            test_name = "chi_square"
            reason = "Categorical association with adequate expected cell counts (>= 5)."

    output = {
        "recommended_test": test_name,
        "reason": reason,
        "assumptions": assumptions,
        "warnings": warnings,
    }

    metrics = [Metric(name="recommended_test", value=test_name)]

    return ToolResult(
        id="",
        tool="recommend_test",
        args={"var1": var1, "var2": var2, "dataset_id": dataset_id},
        status=ToolStatus.ok,
        output=output,
        metrics=metrics,
        warnings=warnings,
    )


@register_tool("stats_test")
@tool_fn("stats_test")
async def stats_test(
    test_name: str,
    dataset_id: str,
    var1: str,
    var2: str,
    alpha: float = 0.05,
    n_tests_in_session: int = 1,
    registry: DatasetRegistry | None = None,
) -> ToolResult:
    """Execute a formal statistical hypothesis test and compute effect sizes and significance."""
    reg = registry or default_registry
    conn = reg.get_connection(dataset_id)
    handle = reg.get(dataset_id)
    tbl = handle.table_name

    df = conn.execute(f'SELECT "{var1}", "{var2}" FROM {tbl}').fetchdf().dropna()

    corrected_alpha = alpha / max(1, n_tests_in_session)
    is_num1 = pd.api.types.is_numeric_dtype(df[var1])

    stat: float = 0.0
    p_val: float = 1.0
    effect_size: float = 0.0
    effect_size_type: str = "none"
    ci: tuple[float, float] | None = None

    if test_name in ("independent_t_test", "welch_t_test", "mann_whitney_u"):
        num_col = var1 if is_num1 else var2
        cat_col = var2 if is_num1 else var1
        groups = [g[num_col].to_numpy() for _, g in df.groupby(cat_col)]
        if len(groups) != 2:
            raise ValueError(f"Test '{test_name}' requires exactly 2 groups, found {len(groups)}")

        g1, g2 = groups[0], groups[1]
        effect_size = _cohens_d(g1, g2)
        effect_size_type = "cohens_d"

        if test_name == "independent_t_test":
            res = stats.ttest_ind(g1, g2, equal_var=True)
            stat, p_val = float(res.statistic), float(res.pvalue)
            ci_res = res.confidence_interval(confidence_level=1.0 - alpha)
            ci = (float(ci_res.low), float(ci_res.high))
        elif test_name == "welch_t_test":
            res = stats.ttest_ind(g1, g2, equal_var=False)
            stat, p_val = float(res.statistic), float(res.pvalue)
            ci_res = res.confidence_interval(confidence_level=1.0 - alpha)
            ci = (float(ci_res.low), float(ci_res.high))
        else:  # mann_whitney_u
            res = stats.mannwhitneyu(g1, g2)
            stat, p_val = float(res.statistic), float(res.pvalue)

    elif test_name in ("one_way_anova", "kruskal_wallis"):
        num_col = var1 if is_num1 else var2
        cat_col = var2 if is_num1 else var1
        groups = [g[num_col].to_numpy() for _, g in df.groupby(cat_col)]
        effect_size = _eta_squared(groups)
        effect_size_type = "eta_squared"

        if test_name == "one_way_anova":
            res = stats.f_oneway(*groups)
            stat, p_val = float(res.statistic), float(res.pvalue)
        else:
            res = stats.kruskal(*groups)
            stat, p_val = float(res.statistic), float(res.pvalue)

    elif test_name in ("chi_square", "fisher_exact"):
        c_table = pd.crosstab(df[var1], df[var2]).to_numpy()
        effect_size = _cramers_v(c_table)
        effect_size_type = "cramers_v"

        if test_name == "chi_square":
            res = stats.chi2_contingency(c_table)
            stat, p_val = float(res[0]), float(res[1])
        else:
            res = stats.fisher_exact(c_table)
            stat, p_val = float(res[0]), float(res[1])

    elif test_name in ("pearson", "spearman"):
        effect_size_type = "r"
        x = df[var1].to_numpy()
        y = df[var2].to_numpy()
        if test_name == "pearson":
            res = stats.pearsonr(x, y)
            stat, p_val = float(res.statistic), float(res.pvalue)
            effect_size = stat
            ci_res = res.confidence_interval(confidence_level=1.0 - alpha)
            ci = (float(ci_res.low), float(ci_res.high))
        else:
            res = stats.spearmanr(x, y)
            stat, p_val = float(res.statistic), float(res.pvalue)
            effect_size = stat

    else:
        raise ValueError(f"Unknown or unsupported statistical test: '{test_name}'")

    is_significant = p_val < corrected_alpha

    sig_str = "statistically significant" if is_significant else "not statistically significant"
    interpretation = (
        f"The test '{test_name}' yielded statistic={stat:.4f}, p-value={p_val:.4e}. "
        f"At alpha={corrected_alpha:.4f} (Bonferroni-adjusted for {n_tests_in_session} test(s)), "
        f"the effect is {sig_str} with {effect_size_type}={effect_size:.4f}."
    )

    output = {
        "test_name": test_name,
        "statistic": round(stat, 4),
        "p_value": p_val,
        "significant": is_significant,
        "alpha": alpha,
        "corrected_alpha": corrected_alpha,
        "effect_size": round(effect_size, 4),
        "effect_size_type": effect_size_type,
        "confidence_interval": ci,
        "interpretation": interpretation,
    }

    metrics = [
        Metric(name="statistic", value=round(stat, 4)),
        Metric(name="p_value", value=p_val),
        Metric(name="effect_size", value=round(effect_size, 4)),
        Metric(name="significant", value=1 if is_significant else 0),
    ]

    return ToolResult(
        id="",
        tool="stats_test",
        args={"test_name": test_name, "var1": var1, "var2": var2, "dataset_id": dataset_id},
        status=ToolStatus.ok,
        output=output,
        metrics=metrics,
    )
