"""Ground truth for income_sql_02: average age of high-income individuals."""

from typing import Any

import pandas as pd


def compute(dataset_path: str) -> dict[str, Any]:
    df = pd.read_csv(dataset_path)
    avg_age = float(df[df["high_income"] == 1]["age"].mean())
    return {
        "question_id": "income_sql_02",
        "expected_answer_type": "numeric",
        "expected_value": round(avg_age, 2),
        "tolerance": {"type": "relative", "value": 0.01},
    }
