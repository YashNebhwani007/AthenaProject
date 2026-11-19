# ADR-15: Granular SQL Metric Extraction

**Status:** Accepted  
**Date:** 2026-11-16  
**Decision:** D15 — Automated tabular metric extraction for SQL query results.

## Context
Athena's `run_sql` tool executes read-only SQL queries via DuckDB. Previously, `run_sql` emitted only `total_rows` and `columns_returned` as `Metric` objects. When the LLM executed aggregations (e.g. `SELECT sex, avg(survived) FROM tbl_titanic GROUP BY sex`), individual cell numbers (e.g. 74.2%, 18.9%) were stored in `output["rows"]` but absent from `metrics`, causing Rule 1 (Numeric Grounding) verifier failures.

## Decision
Implement `_extract_sql_metrics(columns, rows)` in `src/athena/tools/sql.py`:
1. **Single-row queries:** Extract all numeric columns directly as named metrics (e.g., `avg_survived`, `row_count`).
2. **Multi-row queries (<= 50 rows):** Combine categorical grouping labels with numeric column names to produce composite metrics (e.g., `female_survival_rate`, `female_count`, `male_survival_rate`, `male_count`).
3. **Trace Grounding:** Enhance Rule 1 (`check_v1_numeric_grounding`) to recognize cited SQL output table cells.
