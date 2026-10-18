"""Benchmark evaluation runner across systems A1, A2, and B1 per Task 5.2."""

import argparse
import asyncio
import json
import time
from pathlib import Path
from typing import Any

from athena.agent.orchestrator import Orchestrator
from athena.config import Settings
from athena.data import DatasetRegistry
from athena.llm import create_llm_client
from athena.logging import get_logger
from benchmark.baselines.b1_plain_llm import run_b1_baseline
from benchmark.ground_truth.generate import generate_all_ground_truth
from benchmark.scorer import aggregate_scores, score_question

logger = get_logger(__name__)

SMOKE_QUESTIONS = [
    "churn_sql_01",
    "churn_stats_01",
    "churn_model_01",
    "refusal_01",
    "leakage_01",
]


async def run_benchmark(
    systems: list[str],
    repeats: int = 1,
    question_filter: str = "smoke",
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Execute evaluation benchmark across systems and record scores."""
    root = Path(__file__).parent
    out_dir = output_dir or (root / "results")
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load questions and expected ground truth
    questions_file = root / "questions" / "questions.json"
    manifest_file = root / "datasets" / "manifest.json"

    with open(questions_file, encoding="utf-8") as f:
        all_questions = json.load(f)["questions"]

    with open(manifest_file, encoding="utf-8") as f:
        manifest = json.load(f)["datasets"]

    dataset_map = {
        ds["id"]: str((root.parent / ds["path"]).resolve()) for ds in manifest
    }

    expected_gt = generate_all_ground_truth(root)

    # Filter questions
    if question_filter == "smoke":
        selected_questions = [q for q in all_questions if q["id"] in SMOKE_QUESTIONS]
    else:
        selected_questions = all_questions

    registry = DatasetRegistry()
    for ds in manifest:
        registry.register(ds["id"], dataset_map[ds["id"]])

    settings = Settings()
    if not settings.llm_api_key:
        settings.demo_mode = True
    llm_client = create_llm_client(settings)

    benchmark_records: dict[str, Any] = {}
    system_summaries: dict[str, Any] = {}

    for sys_name in systems:
        logger.info("evaluating_system", system=sys_name)
        sys_results: list[dict[str, Any]] = []

        for repeat_idx in range(repeats):
            for q in selected_questions:
                qid = q["id"]
                ds_id = q["dataset_id"]
                ds_path = dataset_map[ds_id]
                gt = expected_gt.get(qid, {})

                start_t = time.time()
                predicted_val = None
                tokens_used = 0

                try:
                    if sys_name == "A1":
                        # Full Athena with Verifier
                        orch = Orchestrator(llm_client=llm_client, registry=registry)
                        run_res = await orch.run(question=q["question"], dataset_id=ds_id)
                        predicted_val = run_res.report.model_dump()
                        tokens_used = run_res.total_tokens

                    elif sys_name == "A2":
                        # Athena without Verifier repair
                        no_repair_cfg = Settings(
                            max_repair_iterations=0,
                            demo_mode=settings.demo_mode,
                        )
                        orch = Orchestrator(
                            llm_client=llm_client,
                            registry=registry,
                            app_settings=no_repair_cfg,
                        )
                        run_res = await orch.run(question=q["question"], dataset_id=ds_id)
                        predicted_val = run_res.report.model_dump()
                        tokens_used = run_res.total_tokens

                    elif sys_name == "B1":
                        # Plain LLM Baseline
                        b1_res = await run_b1_baseline(q["question"], ds_path, llm_client)
                        predicted_val = b1_res.get("raw_result")
                        tokens_used = b1_res.get("tokens", 0)

                except Exception as exc:
                    logger.warning("benchmark_question_failed", qid=qid, error=str(exc))
                    predicted_val = {"error": str(exc)}

                latency_ms = round((time.time() - start_t) * 1000, 2)
                score = score_question(predicted_val, gt)
                score.update({
                    "system": sys_name,
                    "repeat": repeat_idx + 1,
                    "tokens": tokens_used,
                    "runtime_ms": latency_ms,
                })
                sys_results.append(score)

        benchmark_records[sys_name] = sys_results
        system_summaries[sys_name] = aggregate_scores(sys_results)

    # 2. Write results.json
    results_payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "filter": question_filter,
        "repeats": repeats,
        "summaries": system_summaries,
        "details": benchmark_records,
    }
    with open(out_dir / "results.json", "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2)

    # 3. Generate Markdown results table
    date_str = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
    md_lines = [
        "# Athena Benchmark Evaluation Results\n",
        f"**Date:** {date_str} | **Mode:** {question_filter}\n",
        "| System | Accuracy | Hallucination Rate | Refusal Accuracy | Leakage Recall |",
        "|--------|----------|-------------------|------------------|----------------|",
    ]
    for sys_name, summary in system_summaries.items():
        md_lines.append(
            f"| **{sys_name}** | {summary['accuracy'] * 100:.1f}% | "
            f"{summary['hallucination_rate'] * 100:.1f}% | "
            f"{summary['refusal_accuracy'] * 100:.1f}% | "
            f"{summary['leakage_recall'] * 100:.1f}% |"
        )

    with open(out_dir / "results.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    # 4. Generate failure_analysis.md
    fail_lines = ["# Benchmark Failure Analysis\n"]
    for sys_name, records in benchmark_records.items():
        failures = [r for r in records if not r.get("passed")]
        fail_lines.append(f"## System {sys_name} ({len(failures)} failures)\n")
        if not failures:
            fail_lines.append("No failures recorded.\n")
        for f in failures:
            fail_lines.append(
                f"- **{f['question_id']}** ({f.get('answer_type')}): {f.get('issue')}"
            )
        fail_lines.append("")

    with open(out_dir / "failure_analysis.md", "w", encoding="utf-8") as f:
        f.write("\n".join(fail_lines) + "\n")

    return results_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Athena Benchmark Evaluation Runner")
    parser.add_argument(
        "--systems",
        default="A1,A2,B1",
        help="Comma-separated system IDs (A1,A2,B1)",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
        help="Number of repetitions per question",
    )
    parser.add_argument(
        "--questions",
        default="smoke",
        choices=["smoke", "all"],
        help="Question subset",
    )
    args = parser.parse_args()

    systems = [s.strip() for s in args.systems.split(",") if s.strip()]
    asyncio.run(
        run_benchmark(
            systems=systems,
            repeats=args.repeats,
            question_filter=args.questions,
        )
    )


if __name__ == "__main__":
    main()
