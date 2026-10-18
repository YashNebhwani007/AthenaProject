"""Ground truth for multistep_02: correlation + regression on california housing."""

from typing import Any

from benchmark.ground_truth.housing_model_01 import compute as compute_housing


def compute(dataset_path: str) -> dict[str, Any]:
    res = compute_housing(dataset_path)
    res["question_id"] = "multistep_02"
    res["is_multistep"] = True
    return res
