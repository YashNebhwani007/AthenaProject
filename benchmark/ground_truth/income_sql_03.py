"""Ground truth for income_sql_03: high income average hours worked."""

from typing import Any

import pandas as pd


def compute(dataset_path: str) -> dict[str, Any]:
    df = pd.read_csv(dataset_path)
    avg_hours = float(df[df["high_income"] == 1]["hours_per_week"].mean())
    return {
        "question_id": "income_sql_03",
        "expected_answer_type": "numeric",
        "expected_value": round(avg_hours, 4),
        "tolerance": {"type": "relative", "value": 0.01},
        "metadata": {"n_rows": int((df["high_income"] == 1).sum())},
    }
