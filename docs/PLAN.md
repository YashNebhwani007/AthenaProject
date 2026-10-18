# Athena — Master Implementation Plan

**Version:** 1.0 | **Date:** 2026-10-08 | **Author:** Planning Agent

> Each task specifies: what to do, files to create/modify, acceptance criteria, and dependencies.
> An implementing model executes one task at a time without making architectural decisions.
> See also: `docs/adr/` for all resolved decisions, `docs/00-brief-review.md` for assumptions.
> Part 2 (M4-M7) is in `docs/PLAN-part2.md`.

---

## Architecture — File Layout

```
athena/
  AGENTS.md, README.md, pyproject.toml, .env.example, .gitignore, Dockerfile, render.yaml
  docs/ (00-brief-review.md, PLAN.md, PLAN-part2.md, adr/, mcp-usage.md)
  src/athena/
    __init__.py, config.py, schemas.py, logging.py
    llm/    (__init__, base, groq_client, cache)
    data/   (__init__, registry, loaders)
    tools/  (__init__, base, profile, sql, sql_validator, stats, ml, leakage, explain, viz)
    agent/  (__init__, orchestrator, prompts, budget)
    verify/ (__init__, verifier, rules, repair)
    render/ (__init__, renderer)
    api/    (__init__, main, routes, events)
    mcp_server/ (__init__, server)
  benchmark/ (datasets/, questions/, ground_truth/, baselines/, runner, scorer, cache/, results/)
  frontend/  (React + Vite + TypeScript)
  tests/     (conftest, fixtures/, tools/, test_*)
```

---

## M0 — Scaffolding

### Task 0.1 — Initialize Python project

**Do:**
1. Create `pyproject.toml`: name `athena`, Python `>=3.11`, build-system `hatchling`.
   - Dependencies: `fastapi>=0.115,<1`, `uvicorn[standard]>=0.30,<1`, `pydantic>=2.7,<3`, `pydantic-settings>=2.3,<3`, `duckdb>=1.1,<2`, `pandas>=2.2,<3`, `scipy>=1.13,<2`, `statsmodels>=0.14,<1`, `scikit-learn>=1.5,<2`, `lightgbm>=4.4,<5`, `shap>=0.45,<1`, `plotly>=5.22,<6`, `kaleido>=0.2,<1`, `sqlglot>=25,<26`, `httpx>=0.27,<1`, `structlog>=24.1,<25`, `mcp>=1,<3`.
   - Dev extras: `pytest>=8.2,<9`, `pytest-asyncio>=0.23,<1`, `pytest-cov>=5,<6`, `ruff>=0.5,<1`, `pyright>=1.1.370`.
   - Scripts entry point: `athena-mcp = "athena.mcp_server.server:main"`.
   - Ruff config: line-length=100, target-version="py311".
2. Create `.gitignore`: Python, Node, `.env`, `__pycache__`, `.venv`, `data/sessions/`, `benchmark/results/`, `benchmark/cache/`, `*.pkl`, `node_modules/`, `dist/`.
3. Create `.env.example` with all `ATHENA_*` env vars and placeholder values.
4. Create `src/athena/__init__.py` (empty).

**Files:** `pyproject.toml`, `.gitignore`, `.env.example`, `src/athena/__init__.py`
**Accept:** `pip install -e ".[dev]"` succeeds; `ruff check src/` passes.
**Depends:** Nothing.

---

### Task 0.2 — Configuration module

**Do:** Create `src/athena/config.py` using `pydantic_settings.BaseSettings` with `model_config = {"env_prefix": "ATHENA_", "env_file": ".env"}`.

All settings fields with defaults:
- LLM: `llm_provider="groq"`, `llm_model="llama-3.3-70b-versatile"`, `llm_api_key=""`, `llm_base_url="https://api.groq.com/openai/v1"`, `llm_cache_mode="off"`, `llm_max_retries=3`, `llm_seed=42`
- Budgets: `max_steps=30`, `max_tool_calls=20`, `max_tokens=100000`, `timeout_seconds=300`
- Data: `max_file_size_mb=50`, `max_rows=500000`, `max_columns=500`, `sample_rows=5`, `sql_row_limit=10000`, `sql_timeout_seconds=30`, `duckdb_memory_limit="512MB"`
- ML: `random_seed=42`, `shap_max_samples=1000`, `test_size=0.2`, `cv_folds=5`
- Stats: `alpha=0.05`
- Verifier: `max_repair_iterations=2`, `numeric_tolerance_relative=0.01`, `numeric_tolerance_absolute=0.005`
- Server: `host="0.0.0.0"`, `port=8000`, `demo_mode=False`, `demo_max_file_size_mb=5`, `demo_max_rows=50000`
- Paths: `data_dir="data"`, `log_level="INFO"`

Expose module-level `settings = Settings()`.
Create `tests/__init__.py` and `tests/test_config.py`: test defaults load, env var overrides, demo limits.

**Files:** `src/athena/config.py`, `tests/__init__.py`, `tests/test_config.py`
**Accept:** `pytest tests/test_config.py` passes.
**Depends:** 0.1.

---

### Task 0.3 — Core Pydantic schemas

**Do:** Create `src/athena/schemas.py` with Pydantic v2 models:
- `ToolStatus(str, Enum)`: ok, error
- `Metric`: name, value (float|int|str), unit
- `Artifact`: type, ref
- `ToolResult`: id, tool, args, status, output, metrics, artifacts, warnings, runtime_ms
- `ClaimType(str, Enum)`: descriptive, comparative, statistical, predictive, causal
- `EvidenceRef`: tool_result_id, metric
- `Finding`: id, text, claim_type, evidence
- `Confidence(str, Enum)`: low, medium, high
- `Recommendation`: text, supported_by, confidence
- `Report`: question, answerable, tldr, findings, caveats, recommendations
- `VerificationResult`: rule, finding_id, passed, issue, suggestion
- `VerificationSummary`: total_checks, passed, failed, unverified_claims, repairs_attempted, details
- `RunResult`: run_id, session_id, question, report, verification, trace, created_at, total_steps, total_tokens, total_runtime_ms
- `EventType(str, Enum)`: step_started, tool_result, report_draft, verification, final, error, status, clarification_needed

Create `tests/test_schemas.py`: test validation, serialization round-trips, defaults.

**Files:** `src/athena/schemas.py`, `tests/test_schemas.py`
**Accept:** `pytest tests/test_schemas.py` passes.
**Depends:** 0.1.

---

### Task 0.4 — Structured logging

**Do:** Create `src/athena/logging.py`: configure `structlog` with JSON renderer. `get_logger(name)` returns a bound logger. Log level from `settings.log_level`.

**Files:** `src/athena/logging.py`
**Accept:** `get_logger(__name__).info("test", key="val")` outputs valid JSON to stderr.
**Depends:** 0.1, 0.2.

---

### Task 0.5 — LLM client abstraction + Groq + cache

**Do:**
1. `src/athena/llm/base.py`: `LLMResponse` (content, tool_calls, usage, is_final), `ToolCall` (id, name, arguments), `Usage` (prompt_tokens, completion_tokens), `LLMClient` ABC with `async chat(messages, tools, seed) -> LLMResponse`.
2. `src/athena/llm/groq_client.py`: `GroqClient` using `httpx.AsyncClient`. OpenAI-compatible API. Handle 429 with exponential backoff + jitter. Parse tool_calls.
3. `src/athena/llm/cache.py`: `CachedLLMClient` wrapper. Hash = SHA256 of (model, messages, tools, seed). Modes: off/record/replay/auto. Cache dir: `benchmark/cache/{provider}_{model}/`.
4. `src/athena/llm/__init__.py`: `create_llm_client(settings)` factory.

**Note:** Verify Groq API at https://console.groq.com/docs/api-reference before implementing.

**Files:** `src/athena/llm/base.py`, `src/athena/llm/groq_client.py`, `src/athena/llm/cache.py`, `src/athena/llm/__init__.py`
**Accept:** Mocked HTTP tests verify parsing; cache tests verify record/replay.
**Depends:** 0.2, 0.3.

---

### Task 0.6 — Data registry + DuckDB loader

**Do:**
1. `src/athena/data/registry.py`: `ColumnInfo`, `DatasetHandle`, `DatasetRegistry` (register, get_connection, get_schema_summary, get_sample_rows, cleanup).
2. `src/athena/data/loaders.py`: `load_csv()`, `load_parquet()`. Validate limits. DuckDB hardening: `enable_external_access=false`, `lock_configuration=true`, `SET memory_limit`.
3. `src/athena/data/__init__.py`.

**Files:** `src/athena/data/registry.py`, `src/athena/data/loaders.py`, `src/athena/data/__init__.py`
**Accept:** CSV loads, queries work, hardening blocks external access, oversized files rejected.
**Depends:** 0.2.

---

### Task 0.7 — Tool base + registry

**Do:** Create `src/athena/tools/base.py`: `ToolIDGenerator` (returns t1, t2...), `tool_fn(name)` decorator wrapping async functions to return `ToolResult` with timing/error handling, `TOOL_REGISTRY` dict, `register_tool()`.

Create `src/athena/tools/__init__.py`.

**Files:** `src/athena/tools/base.py`, `src/athena/tools/__init__.py`
**Accept:** Dummy tool registers, calls, returns valid `ToolResult`.
**Depends:** 0.3.

---

### Task 0.8 — GitHub Actions CI

**Do:** Create `.github/workflows/ci.yml` (push/PR, Python 3.11+3.12 matrix, ruff+pyright+pytest). Create placeholder `.github/workflows/benchmark-smoke.yml`.

**Files:** `.github/workflows/ci.yml`, `.github/workflows/benchmark-smoke.yml`
**Accept:** Valid YAML.
**Depends:** 0.1.

---

## M1 — Core Tools

### Task 1.1 — profile_dataset tool

**Do:** Create `src/athena/tools/profile.py`: computes row/column counts, per-column stats (dtype, nulls, cardinality, distributions), duplicate rows, constant columns, suspected IDs, suspected targets, data quality warnings (>30% missing, >100 cardinality, constant).

Metrics: `row_count`, `column_count`, `duplicate_rows`, `columns_with_high_missingness`.

Create `tests/fixtures/test_data.csv` (100 rows, known properties), `tests/tools/test_profile.py`.

**Files:** `src/athena/tools/profile.py`, `tests/tools/__init__.py`, `tests/tools/test_profile.py`, `tests/fixtures/test_data.csv`
**Accept:** Assertions pass against hand-verified expectations.
**Depends:** 0.6, 0.7.

---

### Task 1.2 — SQL validator

**Do:** Create `src/athena/tools/sql_validator.py`: `validate_sql(sql) -> ValidationResult` using `sqlglot.parse(sql, dialect="duckdb")`. Whitelist SELECT only. Blacklist INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/COPY/EXPORT/IMPORT/ATTACH/DETACH/INSTALL/LOAD/CALL/PRAGMA/SET. Reject multiple statements.

Create `tests/tools/test_sql_validator.py` with valid and attack cases.

**Files:** `src/athena/tools/sql_validator.py`, `tests/tools/test_sql_validator.py`
**Accept:** All test cases pass.
**Depends:** 0.1.

---

### Task 1.3 — run_sql tool

**Do:** Create `src/athena/tools/sql.py`: validate SQL, inject LIMIT if absent, execute on hardened DuckDB with timeout, return rows + total count.

Output: `{columns, rows, total_rows, truncated}`. Metrics: `total_rows`, `columns_returned`.

Create `tests/tools/test_sql.py`.

**Files:** `src/athena/tools/sql.py`, `tests/tools/test_sql.py`
**Accept:** All tests pass.
**Depends:** 0.6, 0.7, 1.2.

---

### Task 1.4 — recommend_test + stats_test tools

**Do:** Create `src/athena/tools/stats.py` per ADR-06:
- `recommend_test`: deterministic decision tree (normality, variance, group count) recommending test name + reason + assumption results.
- `stats_test`: execute test, return statistic, p-value, effect size (Cohen's d / Cramer's V / eta-squared / r), CI. Bonferroni correction when >1 test.

Create `tests/tools/test_stats.py`.

**Files:** `src/athena/tools/stats.py`, `tests/tools/test_stats.py`
**Accept:** Correct test recommended per scenario. Values match expected.
**Depends:** 0.6, 0.7.

---

### Task 1.5 — Benchmark datasets + first 15 questions

**Do:**
1. `benchmark/datasets/download.py`: download Telco Churn, Adult Income, California Housing as CSV.
2. `benchmark/datasets/manifest.json`.
3. Planted-leakage variant of Telco Churn.
4. `benchmark/questions/questions.json`: 15+ questions (3 SQL, 3 stats, 2 modeling, 2 refusal, 2 causal-trap, 2 leakage, 1 injection).
5. `benchmark/ground_truth/*.py`: ground-truth generator scripts.

**Files:** `benchmark/` directory
**Accept:** Datasets downloaded. Ground-truth scripts produce correct output.
**Depends:** 0.1.

---

## M2 — Orchestrator

### Task 2.1 — Budget tracker

**Do:** Create `src/athena/agent/budget.py`: `Budget` class tracking steps, tool calls, tokens, wall-clock time. Raises `BudgetExhausted` on breach.

Create `tests/test_budget.py`.

**Files:** `src/athena/agent/budget.py`, `src/athena/agent/__init__.py`, `tests/test_budget.py`
**Accept:** All four limits enforced.
**Depends:** 0.2.

---

### Task 2.2 — System prompt + tool schemas

**Do:** Create `src/athena/agent/prompts.py`: `SYSTEM_PROMPT` (role, placeholder syntax, no-compute rule, untrusted data, refusal protocol, Report JSON schema), `build_tool_schemas()`, `build_context_message(handle, profile_result)`.

**Files:** `src/athena/agent/prompts.py`
**Accept:** Prompt comprehensive. Tool schemas valid JSON.
**Depends:** 0.7, 1.1.

---

### Task 2.3 — Orchestrator core loop

**Do:** Create `src/athena/agent/orchestrator.py`: `Orchestrator.run(question) -> RunResult`. Flow: auto-profile, build context, tool-calling loop (dispatch, budget, loop detection), parse Report, verifier stub, return RunResult.

Add CLI entry point. Create `tests/test_orchestrator.py` with mocked LLM.

**Files:** `src/athena/agent/orchestrator.py`, `tests/test_orchestrator.py`
**Accept:** End-to-end with mocked LLM passes.
**Depends:** 0.5, 0.6, 0.7, 1.1, 1.3, 1.4, 2.1, 2.2.

---

## M3 — ML + Leakage + Explain

### Task 3.1 — train_model tool

**Do:** Create `src/athena/tools/ml.py` per ADR-05: auto-detect task type, sklearn Pipeline with ColumnTransformer, three models (Dummy, Linear, LightGBM), held-out eval, 5-fold CV, model pickle storage.

Create `tests/tools/test_ml.py`.

**Files:** `src/athena/tools/ml.py`, `tests/tools/test_ml.py`
**Accept:** Metrics in expected ranges. Tests pass.
**Depends:** 0.6, 0.7.

---

### Task 3.2 — leakage_check tool

**Do:** Create `src/athena/tools/leakage.py`: six named checks (single-feature AUC, correlation, ID columns, train-test duplicates, temporal split, suspicious names). Each returns severity.

Create `tests/tools/test_leakage.py`, `tests/fixtures/test_data_leaky.csv`.

**Files:** `src/athena/tools/leakage.py`, `tests/tools/test_leakage.py`, `tests/fixtures/test_data_leaky.csv`
**Accept:** Detects planted leakage. No false positives on clean data.
**Depends:** 0.6, 0.7.

---

### Task 3.3 — explain_model (SHAP)

**Do:** Create `src/athena/tools/explain.py`: load model by ID, choose correct SHAP explainer, global + local explanations, save plots as PNG.

Create `tests/tools/test_explain.py`.

**Files:** `src/athena/tools/explain.py`, `tests/tools/test_explain.py`
**Accept:** SHAP values computed. Plots saved.
**Depends:** 3.1.

---

### Task 3.4 — make_plot tool

**Do:** Create `src/athena/tools/viz.py`: histogram, bar, box, scatter, correlation_heatmap, shap_summary. Plotly + kaleido PNG export. Text summary.

Create `tests/tools/test_viz.py`.

**Files:** `src/athena/tools/viz.py`, `tests/tools/test_viz.py`
**Accept:** All chart types render. PNGs saved.
**Depends:** 0.6, 0.7.

---

*Continued in `docs/PLAN-part2.md`*
