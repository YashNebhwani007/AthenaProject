"""Ground truth for churn_sql_03: average tenure of churned customers."""

from typing import Any

import pandas as pd


def compute(dataset_path: str) -> dict[str, Any]:
    df = pd.read_csv(dataset_path)
    churned_tenure = float(df[df["churn"] == 1]["tenure"].mean())
    return {
        "question_id": "churn_sql_03",
        "expected_answer_type": "numeric",
        "expected_value": round(churned_tenure, 2),
        "tolerance": {"type": "relative", "value": 0.01},
    }
