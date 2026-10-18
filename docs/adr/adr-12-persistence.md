# ADR-12: Session and Trace Persistence

**Status:** Accepted
**Date:** 2026-10-08
**Decision:** D12 — Persistence of sessions and traces (files vs SQLite).

## Context
Athena needs to store: session metadata, run traces (tool calls + results), reports, and model artifacts. The brief says traces are "stored as JSON." The question is where and how.

## Options

### Option A: File-Based Persistence (Recommended)
JSON files organized in a directory structure.

| Dimension | Assessment |
|-----------|-----------|
| Complexity | Low — just file I/O |
| Queryability | Low — can't easily search across sessions |
| Portability | Excellent — copy a directory, done |
| Dependencies | None |
| Demo deployment | Easy — works on Render's ephemeral filesystem (sessions are transient anyway) |
| Interview showcase | Neutral |

### Option B: SQLite Database
Store sessions and traces in SQLite tables.

| Dimension | Assessment |
|-----------|-----------|
| Complexity | Medium — need schema, migrations, ORM or raw SQL |
| Queryability | Good — SQL queries across sessions |
| Portability | Good — single file |
| Dependencies | Minimal (stdlib sqlite3) |
| Risk | Over-engineering for a single-user demo |

### Option C: DuckDB as Persistence Layer
Reuse DuckDB for both data analysis and metadata storage.

| Dimension | Assessment |
|-----------|-----------|
| Complexity | Medium — blurs the line between data and metadata |
| Risk | High — security hardening for untrusted data conflicts with write access for metadata |

## Decision
**Option A: File-Based Persistence.**

### Directory Structure
```
data/
  sessions/
    {session_id}/
      meta.json           # session metadata (created_at, dataset_name, status)
      dataset.csv          # uploaded file (or symlink to demo data)
      runs/
        {run_id}/
          trace.json       # full execution trace (steps, tool calls, results)
          report.json      # final verified report
          verification.json # verification summary
          artifacts/       # plots, SHAP images
            plot_t5.png
            shap_t7.png
      models/
        {model_id}.pkl     # trained model artifacts (session-scoped)
```

### Session Lifecycle
1. **Create session:** Generate UUID, create directory, copy/link dataset.
2. **Run query:** Create run subdirectory, write trace incrementally (append tool results as they complete).
3. **Fetch results:** Read from files.
4. **Cleanup:** Delete session directory after 24h (API) or on container restart (demo).

### Why Not SQLite
- Single-user portfolio project doesn't need queryability across sessions.
- JSON traces are the primary artifact — they're already files conceptually.
- File-based persistence is the simplest thing that works and matches the brief's "stored as JSON" language.
- If queryability becomes needed later, a thin SQLite index over the JSON files can be added without changing the storage format.

## Consequences
- No database dependency.
- Session data is ephemeral on Render (container restarts lose data) — acceptable for a demo.
- Traces are human-readable JSON files — great for debugging and demonstrations.
- Model artifacts (pickle files) are session-scoped and cleaned up with the session.
