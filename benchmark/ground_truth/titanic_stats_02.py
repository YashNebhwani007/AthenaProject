"""Ground truth for titanic_stats_02: fare difference between 1st and 3rd class."""

from typing import Any

import pandas as pd
from scipy import stats


def compute(dataset_path: str) -> dict[str, Any]:
    df = pd.read_csv(dataset_path)
    c1 = df[df["pclass"] == 1]["fare"].to_numpy()
    c3 = df[df["pclass"] == 3]["fare"].to_numpy()
    res = stats.ttest_ind(c1, c3, equal_var=False)
    p_val = float(res.pvalue)

    return {
        "question_id": "titanic_stats_02",
        "expected_answer_type": "statistical",
        "is_significant": bool(p_val < 0.05),
        "expected_p_value": p_val,
        "tolerance": {"type": "p_value_alpha", "value": 0.05},
    }
