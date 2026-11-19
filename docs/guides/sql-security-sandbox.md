# DuckDB AST Security Sandbox & Validator Specification

Athena implements a multi-tier sandbox for all generated SQL queries to guarantee that
LLM-generated code cannot mutate files, leak server credentials, or execute destructive DDL/DML.

---

## 1. Security Guarantee Overview
Athena enforces three orthogonal layers of security on every SQL execution:
1. **Abstract Syntax Tree (AST) Validation:** Queries parsed via `sqlglot` to verify statement structure.
2. **Read-Only DuckDB Engine Flag:** DuckDB connections opened with `read_only=True` when querying persistent files.
3. **AST Table Isolation & Automatic Aliasing:** All table references redirected to isolated in-memory views.

---

## 2. Forbidden SQL Statement Grammar
The following SQL AST nodes are rejected unconditionally:
- **DDL:** `CREATE`, `ALTER`, `DROP`, `TRUNCATE`, `RENAME`
- **DML:** `INSERT`, `UPDATE`, `DELETE`, `MERGE`
- **TCL:** `COMMIT`, `ROLLBACK`, `SAVEPOINT`
- **Filesystem & Copy:** `COPY ... TO`, `EXPORT DATABASE`, `ATTACH`, `LOAD`
- **System Functions:** `read_csv`, `read_parquet`, `glob`, `pragma` (outside read-only presets)

---

## 3. Query Hardening Pipeline
```
User / LLM SQL String
         │
         ▼
[ sqlglot.parse_one() ] ─── Syntax Error? ───► Reject (ToolStatus.error)
         │
         ▼
[ Walk AST Nodes ] ──────── Contains Forbidden Node? ───► Reject ("Disallowed statement")
         │
         ▼
[ Check / Inject LIMIT ] ── Missing LIMIT? ───► Inject "LIMIT 100"
         │
         ▼
[ DuckDB Connection ] ───── Execute query safely under timeout
```
