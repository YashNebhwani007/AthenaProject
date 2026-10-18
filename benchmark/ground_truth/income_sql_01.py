"""Ground truth for income_sql_01: proportion of high_income == 1."""

from typing import Any

import pandas as pd


def compute(dataset_path: str) -> dict[str, Any]:
    df = pd.read_csv(dataset_path)
    prop = float(df["high_income"].mean())
    return {
        "question_id": "income_sql_01",
        "expected_answer_type": "numeric",
        "expected_value": round(prop, 4),
        "tolerance": {"type": "relative", "value": 0.01},
    }
