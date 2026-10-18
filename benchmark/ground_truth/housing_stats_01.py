"""Ground truth for housing_stats_01: Pearson correlation."""

from typing import Any

import pandas as pd
import scipy.stats as stats


def compute(dataset_path: str) -> dict[str, Any]:
    df = pd.read_csv(dataset_path)
    res = stats.pearsonr(df["medinc"], df["medhouseval"])
    return {
        "question_id": "housing_stats_01",
        "expected_answer_type": "numeric",
        "expected_value": round(float(res.statistic), 4),
        "tolerance": {"type": "absolute", "value": 0.05},
    }
