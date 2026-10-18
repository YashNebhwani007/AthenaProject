"""Ground truth for multistep_03: leakage check + survival model on titanic."""

from typing import Any

from benchmark.ground_truth.titanic_model_01 import compute as compute_titanic


def compute(dataset_path: str) -> dict[str, Any]:
    res = compute_titanic(dataset_path)
    res["question_id"] = "multistep_03"
    res["is_multistep"] = True
    return res
