"""Ground truth for churn_stats_02: contract vs churn Chi-square."""

from typing import Any

import pandas as pd
import scipy.stats as stats


def compute(dataset_path: str) -> dict[str, Any]:
    df = pd.read_csv(dataset_path)
    ct = pd.crosstab(df["contract"], df["churn"]).to_numpy()
    chi2, p_val, _, _ = stats.chi2_contingency(ct)
    return {
        "question_id": "churn_stats_02",
        "expected_answer_type": "statistical",
        "is_significant": bool(p_val < 0.05),
        "expected_p_value": float(p_val),
        "tolerance": {"type": "p_value_alpha", "value": 0.05},
    }
