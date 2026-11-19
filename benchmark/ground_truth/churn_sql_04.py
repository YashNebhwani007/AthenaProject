"""Ground truth for churn_sql_04: paperless billing count."""

from typing import Any

import pandas as pd


def compute(dataset_path: str) -> dict[str, Any]:
    df = pd.read_csv(dataset_path)
    count = int((df["paperless_billing"] == "Yes").sum())
    return {
        "question_id": "churn_sql_04",
        "expected_answer_type": "count",
        "expected_value": count,
        "tolerance": {"type": "absolute", "value": 0},
        "metadata": {"n_rows": len(df)},
    }
