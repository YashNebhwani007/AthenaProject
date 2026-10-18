"""Ground truth for churn_model_01: baseline model ROC-AUC."""

from typing import Any

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split


def compute(dataset_path: str) -> dict[str, Any]:
    df = pd.read_csv(dataset_path)
    X = pd.get_dummies(df[["tenure", "monthly_charges", "contract"]], drop_first=True)
    y = df["churn"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)
    preds = model.predict_proba(X_test)[:, 1]
    auc = float(roc_auc_score(y_test, preds))

    return {
        "question_id": "churn_model_01",
        "expected_answer_type": "metric",
        "expected_metric": "roc_auc",
        "expected_value": round(auc, 3),
        "tolerance": {"type": "relative", "value": 0.10},
    }
