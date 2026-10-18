"""Ground truth for titanic_model_01: baseline accuracy on titanic."""

from typing import Any

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split


def compute(dataset_path: str) -> dict[str, Any]:
    df = pd.read_csv(dataset_path)
    X = pd.get_dummies(df[["pclass", "sex", "age", "fare"]], drop_first=True)
    y = df["survived"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    acc = float(accuracy_score(y_test, preds))

    return {
        "question_id": "titanic_model_01",
        "expected_answer_type": "metric",
        "expected_metric": "accuracy",
        "expected_value": round(acc, 3),
        "tolerance": {"type": "relative", "value": 0.10},
    }
