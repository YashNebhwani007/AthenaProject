"""Ground truth for multistep_01: profile + stats test on telco churn."""

from typing import Any

from benchmark.ground_truth.churn_stats_01 import compute as compute_stats


def compute(dataset_path: str) -> dict[str, Any]:
    res = compute_stats(dataset_path)
    res["question_id"] = "multistep_01"
    res["is_multistep"] = True
    return res
