"""Ground truth for titanic_sql_01: overall survival rate."""

from typing import Any

import pandas as pd


def compute(dataset_path: str) -> dict[str, Any]:
    df = pd.read_csv(dataset_path)
    rate = float(df["survived"].mean())
    return {
        "question_id": "titanic_sql_01",
        "expected_answer_type": "numeric",
        "expected_value": round(rate, 4),
        "tolerance": {"type": "relative", "value": 0.01},
    }
