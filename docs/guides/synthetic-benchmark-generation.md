# Synthetic Benchmark Ground Truth Generation Guide

Athena benchmarks evaluate agent systems (A1, A2, B1) against mathematically exact ground truth.
This guide outlines how ground truth values are synthesized, computed, and validated.

---

## 1. Generation Pipeline Architecture
All ground truth scripts are located in `benchmark/ground_truth/`:
- `churn_sql_01.py` through `churn_sql_05.py`: Exact numeric aggregations computed via DuckDB.
- `churn_stats_01.py` through `churn_stats_05.py`: $p$-values and effect sizes computed via SciPy.
- `churn_model_01.py`: Deterministic scikit-learn LogisticRegression reference scores.
- `refusal_01.py` through `refusal_05.py`: Questions requiring refusal (unanswerable or unethical).
- `leakage_01.py`: Synthetic datasets with planted future-dated features.

---

## 2. Deterministic Reproducibility
To ensure ground truth remains constant across CI environments:
1. `np.random.seed(42)` is seeded at the top of every generation routine.
2. DuckDB deterministic query execution: `ORDER BY` clauses are explicitly attached to all aggregations.
3. Floating point tolerances:
   - Relative tolerance: $\le 1.0\%$
   - Absolute tolerance: $\le 0.005$

---

## 3. Regenerating Ground Truth
To regenerate `expected.json` after updating question definitions:
```bash
python -m benchmark.ground_truth.generate
```
All outputs are serialized to `benchmark/ground_truth/expected.json` with SHA-256 integrity verification.
