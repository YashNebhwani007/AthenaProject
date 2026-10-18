"""Ground truth for housing_model_01: baseline regression RMSE."""

from typing import Any

import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import root_mean_squared_error
from sklearn.model_selection import train_test_split


def compute(dataset_path: str) -> dict[str, Any]:
    df = pd.read_csv(dataset_path)
    feature_cols = [c for c in df.columns if c != "medhouseval"]
    X = df[feature_cols]
    y = df["medhouseval"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = Ridge()
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    rmse = float(root_mean_squared_error(y_test, preds))

    return {
        "question_id": "housing_model_01",
        "expected_answer_type": "metric",
        "expected_metric": "rmse",
        "expected_value": round(rmse, 3),
        "tolerance": {"type": "relative", "value": 0.15},
    }
