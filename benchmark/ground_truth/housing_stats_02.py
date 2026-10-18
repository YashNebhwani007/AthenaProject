"""Ground truth for housing_stats_02: median house value difference by age group."""

from typing import Any

import pandas as pd
from scipy import stats


def compute(dataset_path: str) -> dict[str, Any]:
    df = pd.read_csv(dataset_path)
    old = df[df["houseage"] > 30]["medhouseval"].to_numpy()
    young = df[df["houseage"] <= 30]["medhouseval"].to_numpy()
    res = stats.ttest_ind(old, young, equal_var=False)
    p_val = float(res.pvalue)

    return {
        "question_id": "housing_stats_02",
        "expected_answer_type": "statistical",
        "is_significant": bool(p_val < 0.05),
        "expected_p_value": p_val,
        "tolerance": {"type": "p_value_alpha", "value": 0.05},
    }
