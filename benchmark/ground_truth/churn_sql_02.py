"""Ground truth for churn_sql_02: Month-to-month contract count."""

from typing import Any

import pandas as pd


def compute(dataset_path: str) -> dict[str, Any]:
    df = pd.read_csv(dataset_path)
    count = int((df["contract"] == "Month-to-month").sum())
    return {
        "question_id": "churn_sql_02",
        "expected_answer_type": "count",
        "expected_value": count,
        "tolerance": {"type": "exact", "value": 0},
    }
