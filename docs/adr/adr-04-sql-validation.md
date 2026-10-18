# ADR-04: SQL Validation Strategy

**Status:** Accepted
**Date:** 2026-10-08
**Decision:** D4 — SQL validation: AST parsing library vs engine-level restrictions vs both.

## Context
The LLM generates SQL queries. These must be validated as SELECT-only (no INSERT, UPDATE, DELETE, DROP, etc.) and executed with resource limits. Two layers of defense are possible.

## Options

### Option A: AST Parsing Only
Use `sqlglot` to parse and validate SQL before execution.

| Dimension | Assessment |
|-----------|-----------|
| Complexity | Low-medium — sqlglot is well-maintained and DuckDB-aware |
| Security | Good — catches most dangerous statements before execution |
| Risk | Medium — parser might not catch all DuckDB-specific syntax (e.g., COPY, EXPORT) |
| Performance | Fast — parsing is negligible |

### Option B: Engine-Level Restrictions Only
Rely on DuckDB's security settings (read-only mode, disabled external access, locked configuration).

| Dimension | Assessment |
|-----------|-----------|
| Complexity | Low — configuration-only |
| Security | Good — DuckDB enforces restrictions at execution time |
| Risk | Medium — error messages from blocked operations may confuse the LLM |
| Performance | No overhead |

### Option C: Both — AST Parsing + Engine-Level Restrictions (Recommended)
Parse with `sqlglot` first, then execute in a hardened DuckDB connection.

| Dimension | Assessment |
|-----------|-----------|
| Complexity | Medium — two layers, but each is simple |
| Security | Excellent — defense in depth |
| Risk | Low — if parser misses something, engine catches it |
| Interview showcase | Strong — demonstrates security-in-depth thinking |
| Performance | Negligible overhead |

## Decision
**Option C: Both layers.**

Implementation:

1. **AST Validation (sqlglot):**
   - Parse SQL with `sqlglot.parse(sql, dialect="duckdb")`
   - Whitelist: only `SELECT` statements allowed
   - Blacklist keywords in any position: `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `COPY`, `EXPORT`, `IMPORT`, `ATTACH`, `DETACH`, `INSTALL`, `LOAD`, `CALL`, `PRAGMA`, `SET`
   - Reject multiple statements (no semicolon-separated batches)
   - Reject subqueries that contain non-SELECT operations

2. **DuckDB Hardening (verified from DuckDB docs 2026-10-08):**
   ```python
   conn = duckdb.connect(database=':memory:')
   conn.execute("SET enable_external_access = false")
   conn.execute("SET lock_configuration = true")  # prevents re-enabling
   ```
   - Plus: row limit via `LIMIT` injection (if not present, wrap in `SELECT * FROM (...) LIMIT {max_rows}`)
   - Plus: execution timeout via Python-level `asyncio.wait_for`
   - Plus: memory limit via DuckDB's `SET memory_limit`

3. **Error reporting:** Validation errors returned as structured `ToolResult` with `status: "error"` and clear message for the LLM to retry with corrected SQL.

## Consequences
- `sqlglot` is added as a dependency (well-maintained, MIT license, ~1MB).
- Two-layer validation means a bypass requires defeating both layers.
- Benchmark should include adversarial SQL cases (injection attempts in questions).
