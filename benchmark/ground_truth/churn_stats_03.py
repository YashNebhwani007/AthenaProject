"""Ground truth for churn_stats_03: Pearson r between tenure and total_charges."""

from typing import Any

import pandas as pd
from scipy import stats


def compute(dataset_path: str) -> dict[str, Any]:
    df = pd.read_csv(dataset_path)
    r_val, p_val = stats.pearsonr(df["tenure"], df["total_charges"])
    return {
        "question_id": "churn_stats_03",
        "expected_answer_type": "numeric",
        "expected_value": round(float(r_val), 4),
        "tolerance": {"type": "relative", "value": 0.05},
        "p_value": float(p_val),
    }
