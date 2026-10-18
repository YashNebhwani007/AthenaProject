"""Ground truth for housing_sql_02: count of blocks with population > 5000."""

from typing import Any

import pandas as pd


def compute(dataset_path: str) -> dict[str, Any]:
    df = pd.read_csv(dataset_path)
    count_val = int((df["population"] > 5000).sum())
    return {
        "question_id": "housing_sql_02",
        "expected_answer_type": "count",
        "expected_value": count_val,
        "tolerance": {"type": "exact"},
    }
