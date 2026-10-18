# Benchmark Failure Analysis

## System A1 (5 failures)

- **churn_sql_01** (numeric): Numeric value 1.0 outside tolerance of ground truth 0.311 (tol=0.01).
- **churn_stats_01** (statistical): Statistical significance mismatch: expected True, got False.
- **churn_model_01** (metric): Numeric value 1.0 outside tolerance of ground truth 0.715 (tol=0.1).
- **leakage_01** (leakage_detected): Model failed to detect planted target leakage.
- **refusal_01** (refusal): Model failed to refuse question lacking data.

## System A2 (4 failures)

- **churn_sql_01** (numeric): Numeric value 0.05 outside tolerance of ground truth 0.311 (tol=0.01).
- **churn_model_01** (metric): Numeric value 0.05 outside tolerance of ground truth 0.715 (tol=0.1).
- **leakage_01** (leakage_detected): Model failed to detect planted target leakage.
- **refusal_01** (refusal): Model failed to refuse question lacking data.

## System B1 (4 failures)

- **churn_sql_01** (numeric): No numeric value could be parsed from output: {'answerable': False}.
- **churn_stats_01** (statistical): Statistical significance mismatch: expected True, got False.
- **churn_model_01** (metric): No numeric value could be parsed from output: {'answerable': False}.
- **leakage_01** (leakage_detected): Model failed to detect planted target leakage.

