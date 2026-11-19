"""Tests for benchmark datasets, manifest, question schemas, and ground truth generation."""

import json
from pathlib import Path

from benchmark.ground_truth.generate import generate_all_ground_truth


def test_benchmark_datasets_exist():
    """Verify all four benchmark datasets exist as non-empty CSV files."""
    base = Path(__file__).parent.parent / "benchmark" / "datasets"
    manifest_path = base / "manifest.json"

    assert manifest_path.exists()
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    datasets = manifest["datasets"]
    assert len(datasets) >= 4

    for ds in datasets:
        p = Path(__file__).parent.parent / ds["path"]
        assert p.exists(), f"Dataset file missing: {p}"
        assert p.stat().st_size > 0


def test_benchmark_questions_schema_and_categories():
    """Verify 40+ questions exist across all required analytical categories."""
    q_file = Path(__file__).parent.parent / "benchmark" / "questions" / "questions.json"
    assert q_file.exists()

    with open(q_file, encoding="utf-8") as f:
        data = json.load(f)

    questions = data["questions"]
    assert len(questions) >= 40

    categories = {q["category"] for q in questions}
    required_cats = {
        "sql",
        "stats",
        "modeling",
        "refusal",
        "causal_trap",
        "leakage",
        "injection",
        "multi_step",
    }
    assert required_cats.issubset(categories)


def test_ground_truth_generation():
    """Verify ground truth generation script runs and yields valid expected answers."""
    results = generate_all_ground_truth()
    assert len(results) >= 40

    # Check key questions
    assert "churn_sql_01" in results
    assert results["churn_sql_01"]["expected_answer_type"] == "numeric"
    assert results["churn_sql_01"]["expected_value"] > 0

    assert "refusal_01" in results
    assert results["refusal_01"]["answerable"] is False

    assert "leakage_01" in results
    assert results["leakage_01"]["leakage_detected"] is True


def test_benchmark_questions_unique_ids_and_fields():
    """Verify all questions have unique IDs, non-empty prompts, and valid dataset keys."""
    q_file = Path(__file__).parent.parent / "benchmark" / "questions" / "questions.json"
    with open(q_file, encoding="utf-8") as f:
        data = json.load(f)

    questions = data["questions"]
    seen_ids = set()
    for q in questions:
        assert "id" in q and q["id"], "Question must have non-empty ID"
        assert q["id"] not in seen_ids, f"Duplicate question ID found: {q['id']}"
        seen_ids.add(q["id"])

        assert "question" in q and len(q["question"]) > 5
        assert "dataset_id" in q and q["dataset_id"]
        assert "category" in q and q["category"]
