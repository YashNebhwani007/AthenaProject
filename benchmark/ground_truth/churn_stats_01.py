"""Ground truth for churn_stats_01: t-test / Mann-Whitney on monthly charges."""

from typing import Any

import pandas as pd
import scipy.stats as stats


def compute(dataset_path: str) -> dict[str, Any]:
    df = pd.read_csv(dataset_path)
    churn0 = df[df["churn"] == 0]["monthly_charges"].to_numpy()
    churn1 = df[df["churn"] == 1]["monthly_charges"].to_numpy()
    res = stats.ttest_ind(churn0, churn1, equal_var=False)
    p_val = float(res.pvalue)

    return {
        "question_id": "churn_stats_01",
        "expected_answer_type": "statistical",
        "is_significant": bool(p_val < 0.05),
        "expected_p_value": p_val,
        "tolerance": {"type": "p_value_alpha", "value": 0.05},
    }
