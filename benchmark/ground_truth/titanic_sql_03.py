"""Ground truth for titanic_sql_03: first class average fare."""

from typing import Any

import pandas as pd


def compute(dataset_path: str) -> dict[str, Any]:
    df = pd.read_csv(dataset_path)
    avg_fare = float(df[df["pclass"] == 1]["fare"].mean())
    return {
        "question_id": "titanic_sql_03",
        "expected_answer_type": "numeric",
        "expected_value": round(avg_fare, 4),
        "tolerance": {"type": "relative", "value": 0.01},
        "metadata": {"n_rows": int((df["pclass"] == 1).sum())},
    }
