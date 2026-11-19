# AST SQLGlot Custom Transpilation for DuckDB Dialect

## Overview
Athena accepts user-authored and LLM-generated SQL queries across multiple dialect styles
(PostgreSQL, SQLite, MySQL, Snowflake). To guarantee deterministic execution against the underlying
DuckDB analytical storage engine without runtime dialect syntax errors, Athena parses and transpiles
all SQL ASTs using `sqlglot`.

## Transpilation Pipeline

```
[Raw SQL Query]
       │
       ▼
[sqlglot.parse_one(read="postgres" | "sqlite")]
       │
       ▼
[AST Validation: Read-Only & Disallowed Functions]
       │
       ▼
[sqlglot.transpile(write="duckdb")]
       │
       ▼
[DuckDB Connection Execution]
```

## Handled Dialect Differences
1. **Date/Time Arithmetic:** `INTERVAL '1 day'` transpiled cleanly into DuckDB date interval types.
2. **String Concatenation:** Translates MySQL `CONCAT(a, b)` and SQLite `a || b` uniformly.
3. **Regex Matching:** Maps `REGEXP` and `~` to DuckDB's `regexp_matches()` functions.
4. **Division Semantics:** Handles integer division casting (`x / y` vs `x::DOUBLE / y`).
