"""Ground truth for housing_sql_01: maximum medhouseval."""

from typing import Any

import pandas as pd


def compute(dataset_path: str) -> dict[str, Any]:
    df = pd.read_csv(dataset_path)
    val = float(df["medhouseval"].max())
    return {
        "question_id": "housing_sql_01",
        "expected_answer_type": "numeric",
        "expected_value": round(val, 4),
        "tolerance": {"type": "relative", "value": 0.001},
    }
