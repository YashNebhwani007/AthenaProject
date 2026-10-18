# ADR-11: Multi-Table Datasets

**Status:** Accepted
**Date:** 2026-10-08
**Decision:** D11 — Multi-table datasets: in scope or not for v1.

## Options

### Option A: Single-Table Only for v1 (Recommended)
Only support a single CSV/Parquet file per session.

| Dimension | Assessment |
|-----------|-----------|
| Complexity | Low — no join logic, no schema resolution |
| Risk | Low — well-defined scope |
| User impact | Acceptable — most portfolio demo scenarios use single tables |
| Interview showcase | Neutral — focus depth on other features is more impressive |

### Option B: Multi-Table with Explicit Joins
Allow multiple file uploads, auto-detect foreign keys, let LLM write JOINs.

| Dimension | Assessment |
|-----------|-----------|
| Complexity | Very high — FK detection, join validation, schema resolution |
| Risk | Very high — scope explosion, hard to test, hard to demo |
| Time cost | 3-5 extra days minimum |

### Option C: Multi-Table as v1.1 Extension
Design the data layer to accommodate it, but don't implement.

| Dimension | Assessment |
|-----------|-----------|
| Complexity | Low — just ensure the DatasetHandle abstraction can be extended |
| Risk | Low |

## Decision
**Option A: Single-Table Only for v1, with Option C's extensibility.**

The `DatasetHandle` will reference a single DuckDB table name. The interface is designed so that a future version could register multiple tables in the same DuckDB connection, but v1 enforces one file = one table.

Explicitly out of scope for v1:
- Multiple file uploads per session
- JOIN queries across tables
- Foreign key detection
- Star/snowflake schema support

## Consequences
- Simple, well-scoped data layer.
- No impact on the demo (all benchmark datasets are single tables).
- Future extension is possible without refactoring.
