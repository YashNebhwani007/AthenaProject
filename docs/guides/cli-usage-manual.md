# Athena CLI Usage Reference Manual

The `athena` command-line utility provides rapid deterministic data profiling, SQL exploration,
and target leakage auditing directly from your terminal.

---

## 1. Installation & Availability
When Athena is installed in editable mode or via wheel:
```bash
pip install -e .
athena --help
```

---

## 2. Command Reference

### A. Dataset Profiling (`athena profile`)
Analyzes dataset dimensions, schema datatypes, and null value percentages.

```bash
# Print formatted human-readable summary
athena profile benchmark/datasets/telco_churn.csv

# Emit raw structured JSON for piping into jq
athena profile benchmark/datasets/telco_churn.csv --json | jq .row_count
```

### B. Read-Only SQL Querying (`athena query`)
Executes an AST-validated SQL query against a local CSV or Parquet file using DuckDB.

```bash
# Query the file using the 'data' table alias
athena query benchmark/datasets/titanic.csv \
  --sql "SELECT pclass, sex, avg(survived) FROM data GROUP BY pclass, sex ORDER BY pclass, sex"

# Limit output rows
athena query benchmark/datasets/california_housing.csv \
  --sql "SELECT medinc, medhouseval FROM data WHERE medinc > 8.0" \
  --limit 10
```

### C. Data Leakage Auditing (`athena audit-leakage`)
Runs Athena's 6 deterministic leakage checks against a specified target column.

```bash
athena audit-leakage benchmark/datasets/telco_churn_leakage.csv --target churn
```
