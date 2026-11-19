# ADR-26: DuckDB Memory Limit and Disk Spill Policy

## Status
Accepted

## Context
DuckDB provides exceptionally fast analytical execution, but uncontrolled in-memory buffers
can lead to Out-Of-Memory (OOM) crashes in memory-constrained cloud environments (e.g. 512MB to 2GB container tiers).
A clear policy is required to govern memory ceiling allocation and temporary spill-to-disk directories.

## Decision
1. Explicitly configure DuckDB connection parameters during registry initialization:
   - `SET max_memory = '1GB'` (configurable via `Settings.duckdb_memory_limit`).
   - `SET preserve_insertion_order = false` to optimize vector processing throughput.
2. Establish a designated temporary spill directory under `data/duckdb_temp/` cleaned up on session termination.
3. For multi-gigabyte queries, DuckDB transparently offloads intermediate sort and hash aggregation buffers to NVMe/SSD storage.

## Consequences
- Guaranteed stability against system-level container OOM termination.
- Queries that exceed RAM limits succeed via controlled disk spill rather than crashing.
- Temporary files are reliably purged during session garbage collection.
