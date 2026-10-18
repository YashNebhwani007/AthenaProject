"""Ground truth for titanic_sql_02: count of surviving female passengers."""

from typing import Any

import pandas as pd


def compute(dataset_path: str) -> dict[str, Any]:
    df = pd.read_csv(dataset_path)
    count_val = int(((df["sex"] == "female") & (df["survived"] == 1)).sum())
    return {
        "question_id": "titanic_sql_02",
        "expected_answer_type": "count",
        "expected_value": count_val,
        "tolerance": {"type": "exact"},
    }
