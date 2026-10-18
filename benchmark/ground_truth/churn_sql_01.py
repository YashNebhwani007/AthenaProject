"""Ground truth for churn_sql_01: overall churn rate."""

from typing import Any

import pandas as pd


def compute(dataset_path: str) -> dict[str, Any]:
    df = pd.read_csv(dataset_path)
    churn_rate = float(df["churn"].mean())
    return {
        "question_id": "churn_sql_01",
        "expected_answer_type": "numeric",
        "expected_value": round(churn_rate, 4),
        "tolerance": {"type": "relative", "value": 0.01},
        "metadata": {"n_rows": len(df)},
    }
