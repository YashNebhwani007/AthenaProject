# ADR-25: Multi-Table Join AST Validation and Schema Reflection

## Status
Accepted

## Context
When multi-table datasets are loaded into Athena, queries may involve `JOIN`, `LEFT JOIN`, or `CROSS JOIN`
operations. Without strict AST validation, joining unrelated tables can cause accidental Cartesian products,
memory exhaustion, or cross-tenant data leakage if table references are not properly isolated.

## Decision
1. Validate all join conditions in SQL queries using sqlglot's Abstract Syntax Tree parser.
2. Require explicit `ON` clauses for all inner and outer joins; prohibit unbounded `CROSS JOIN` operations.
3. Automatically alias table references with dataset-specific prefixes (`t1_`, `t2_`) to prevent column name collisions.
4. Extract join cardinality estimates prior to execution; abort queries if the predicted result set exceeds DuckDB memory limits.

## Consequences
- Prevents runaway Cartesian explosions on multi-table exploratory queries.
- Guarantees deterministic column disambiguation when tables share identical feature names.
- Maintains strict read-only guarantees across multi-table query plans.
