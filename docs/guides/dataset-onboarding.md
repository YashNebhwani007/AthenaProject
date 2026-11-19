# Dataset Onboarding Guide

Athena supports analytical workloads on structured tabular datasets in **CSV** and **Parquet** formats.

## 1. Supported Formats & Constraints

| Parameter | Default Constraint | Configuration Key |
|---|---|---|
| Maximum File Size | 50 MB | `ATHENA_MAX_FILE_SIZE_MB` |
| Maximum Rows | 500,000 | `ATHENA_MAX_ROWS` |
| Maximum Columns | 500 | `ATHENA_MAX_COLUMNS` |
| Formats | `.csv`, `.parquet`, `.pq` | — |

## 2. Ingestion Pipeline

1. **Secure DuckDB Sandbox:** Files are mounted directly into hardened in-memory DuckDB connections with filesystem write restrictions disabled.
2. **Schema Inference:** Column data types, sample values, and cardinality are deterministically measured.
3. **Table View Aliasing:** A canonical table name (e.g. `tbl_churn`) and an alias matching the dataset ID (`churn`) are registered in DuckDB.
4. **Data Quality Profiling:** Automatic identification of missingness (>30%), duplicate rows, single-value columns, and suspected targets.
