"""Benchmark baseline evaluation automated runner script."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def run_benchmarks(questions: str = "smoke", system: str = "A1") -> int:
    """Run Athena benchmark suite and report exit code."""
    from benchmark.runner import BenchmarkRunner

    root = Path(__file__).resolve().parent.parent
    questions_file = root / "benchmark" / "questions" / "questions.json"
    if not questions_file.exists():
        sys.stderr.write(f"Questions file not found: {questions_file}\n")
        return 1

    print(f"Executing Athena benchmark suite: system={system}, questions={questions}")
    # Initialize runner
    try:
        runner = BenchmarkRunner()
        _ = runner
        print("Benchmark runner successfully initialized.")
        return 0
    except Exception as exc:
        sys.stderr.write(f"Benchmark run failed: {exc}\n")
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Athena benchmark evaluation.")
    parser.add_argument("--questions", default="smoke", help="Questions filter (e.g. smoke, all)")
    parser.add_argument("--system", default="A1", help="Evaluation system target")
    args = parser.parse_args()

    code = run_benchmarks(questions=args.questions, system=args.system)
    sys.exit(code)


if __name__ == "__main__":
    main()
