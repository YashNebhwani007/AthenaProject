# ADR-38: DuckDB Parquet Row-Group Pushdown Optimization

## Status
Accepted

## Context
As dataset sizes grow to millions of rows, full scans of CSV or unpartitioned tables degrade
SQL query execution times and increase memory footprint in the DuckDB analytics engine.
Parquet storage formats support columnar projection and row-group filter pushdown.

## Decision
1. For uploaded datasets exceeding 50MB or 500,000 rows, automatically convert raw CSV inputs into
   snappy-compressed Parquet files in the Athena dataset store.
2. Configure DuckDB queries with `PRAGMA enable_object_cache=true` and exploit statistics-based
   row-group pruning on filtered numeric and date columns.
3. Preserve original column types and datetime precisions during the conversion step.

## Consequences
- Up to 10x query execution speedup for aggregate and filtered SQL queries on large datasets.
- 60-80% reduction in local disk storage and RAM consumption.
- Completely transparent to end users and orchestrator tool invocations.
