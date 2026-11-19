# ADR-19: DuckDB Table Aliasing and AST Safety

**Status:** Accepted  
**Date:** 2026-11-15  
**Decision:** D19 — Table view aliasing and SQL AST validation.

## Context
When users or LLMs formulate SQL queries, they often write `FROM titanic` instead of the canonical `FROM tbl_titanic`. Simultaneously, queries must be strictly checked for read-only semantics to prevent arbitrary data modifications or exfiltration.

## Decision
1. **View Aliasing:** When registering a dataset in `DatasetRegistry`, create a secondary view alias `clean_alias` matching `dataset_id`. Queries referencing either the prefixed table or the raw dataset name resolve identically.
2. **AST Parsing:** Use `sqlglot` to validate that every executed statement is a `Select` expression, reject destructive operations (`Drop`, `Delete`, `Insert`), and automatically inject a hardened `LIMIT` clause.
