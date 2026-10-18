"""Generate benchmark ground truth expected values using deterministic scripts."""

import importlib
import json
from pathlib import Path
from typing import Any


def generate_all_ground_truth(base_dir: Path | None = None) -> dict[str, Any]:
    """Execute all ground-truth scripts and compile benchmark/ground_truth/expected.json."""
    root = base_dir or Path(__file__).parent.parent
    questions_file = root / "questions" / "questions.json"
    manifest_file = root / "datasets" / "manifest.json"

    with open(questions_file, encoding="utf-8") as f:
        questions_data = json.load(f)

    with open(manifest_file, encoding="utf-8") as f:
        manifest_data = json.load(f)

    # Map dataset_id to dataset absolute path
    dataset_paths = {
        ds["id"]: str((root.parent / ds["path"]).resolve())
        for ds in manifest_data["datasets"]
    }

    expected_results: dict[str, Any] = {}

    for q in questions_data["questions"]:
        qid = q["id"]
        script_file = q["expected_ground_truth_script"]
        module_name = f"benchmark.ground_truth.{Path(script_file).stem}"
        ds_id = q["dataset_id"]
        ds_path = dataset_paths.get(ds_id, "")

        mod = importlib.import_module(module_name)
        if not hasattr(mod, "compute"):
            raise AttributeError(f"Module {module_name} does not expose compute()")

        result = mod.compute(ds_path)
        expected_results[qid] = result

    out_file = root / "ground_truth" / "expected.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(expected_results, f, indent=2)

    return expected_results


if __name__ == "__main__":
    results = generate_all_ground_truth()
    print(f"Generated ground truth for {len(results)} questions successfully.")
