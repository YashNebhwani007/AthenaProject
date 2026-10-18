"""Ground truth for churn_model_02: top SHAP feature on telco_churn."""

from typing import Any


def compute(_dataset_path: str) -> dict[str, Any]:
    return {
        "question_id": "churn_model_02",
        "expected_answer_type": "categorical",
        "expected_value": "contract",
        "acceptable_values": ["contract", "contract_Month-to-month", "tenure", "monthly_charges"],
    }
