"""Ground truth for titanic_stats_01: survival rate difference between sexes."""

from typing import Any

import pandas as pd
from scipy import stats


def compute(dataset_path: str) -> dict[str, Any]:
    df = pd.read_csv(dataset_path)
    contingency = pd.crosstab(df["sex"], df["survived"])
    res = stats.chi2_contingency(contingency)
    p_val = float(res.pvalue)

    return {
        "question_id": "titanic_stats_01",
        "expected_answer_type": "statistical",
        "is_significant": bool(p_val < 0.05),
        "expected_p_value": p_val,
        "direction": "higher",
        "tolerance": {"type": "p_value_alpha", "value": 0.05},
    }
