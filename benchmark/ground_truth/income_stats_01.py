"""Ground truth for income_stats_01: age difference by income class."""

from typing import Any

import pandas as pd
from scipy import stats


def compute(dataset_path: str) -> dict[str, Any]:
    df = pd.read_csv(dataset_path)
    high = df[df["high_income"] == 1]["age"].to_numpy()
    low = df[df["high_income"] == 0]["age"].to_numpy()
    res = stats.ttest_ind(high, low, equal_var=False)
    p_val = float(res.pvalue)

    return {
        "question_id": "income_stats_01",
        "expected_answer_type": "statistical",
        "is_significant": bool(p_val < 0.05),
        "expected_p_value": p_val,
        "direction": "higher",
        "tolerance": {"type": "p_value_alpha", "value": 0.05},
    }
