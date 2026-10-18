"""Ground truth for housing_sql_03: average house age."""

from typing import Any

import pandas as pd


def compute(dataset_path: str) -> dict[str, Any]:
    df = pd.read_csv(dataset_path)
    avg_age = float(df["houseage"].mean())
    return {
        "question_id": "housing_sql_03",
        "expected_answer_type": "numeric",
        "expected_value": round(avg_age, 2),
        "tolerance": {"type": "relative", "value": 0.01},
    }
