"""Ground truth for housing_model_02: R2 score on california housing."""

from typing import Any

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split


def compute(dataset_path: str) -> dict[str, Any]:
    df = pd.read_csv(dataset_path)
    X = df.drop(columns=["medhouseval"])
    y = df["medhouseval"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LinearRegression()
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    r2 = float(r2_score(y_test, preds))

    return {
        "question_id": "housing_model_02",
        "expected_answer_type": "metric",
        "expected_metric": "r2",
        "expected_value": round(r2, 3),
        "tolerance": {"type": "relative", "value": 0.15},
    }
