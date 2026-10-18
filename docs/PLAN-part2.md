# Athena — Master Implementation Plan (Part 2: M4-M7)

*Continued from `docs/PLAN.md`*

---

## M4 — Verifier

### Task 4.1 — Verifier rules V1-V5

**Do:** Create `src/athena/verify/rules.py` with one function per rule:

- **`check_v1_numeric_grounding(report, tool_results)`**: Find all `{{...}}` placeholders and verify they resolve to existing metrics. Find literal numbers in finding text (regex) and check against cited metrics with tolerance (1% relative or 0.005 absolute). Maintain an allowed-literals list (config constants like 0.05, 5, 10).

- **`check_v2_claim_evidence_consistency(report, tool_results)`**: "Significant" requires p < alpha (after correction). Direction words ("higher"/"lower") must match effect sign. Strength words mapped to thresholds: correlation |r|>0.7="strong", 0.3-0.7="moderate", <0.3="weak"; Cohen's d >0.8="large", 0.5-0.8="medium", <0.5="small". Performance claims must cite held-out metrics.

- **`check_v3_causal_language(report)`**: Scan for causal keywords ("causes", "caused by", "leads to", "results in", "due to", "because of", "effect of"). Flag if claim_type is not causal or if no experimental evidence.

- **`check_v4_linkage(report, tool_results)`**: Every finding has evidence. Every recommendation links to findings. Every evidence tool_result_id exists in trace.

- **`check_v5_data_quality_propagation(report, tool_results)`**: High-severity leakage requires caveat and model metrics flagged. Missingness >30% in used columns requires caveat.

Each returns `list[VerificationResult]`.

Create `src/athena/verify/__init__.py`.
Create `tests/test_verifier_rules.py`: 3+ pass and 3+ fail cases per rule. Edge cases: empty findings, empty recommendations.

**Files:** `src/athena/verify/rules.py`, `src/athena/verify/__init__.py`, `tests/test_verifier_rules.py`
**Accept:** All rule tests pass. Each rule catches violations and passes valid reports.
**Depends:** 0.3.

---

### Task 4.2 — Verifier entry point + repair loop + renderer

**Do:**
1. Create `src/athena/verify/verifier.py`: `Verifier.verify(report, tool_results, llm_client) -> (Report, VerificationSummary)`. Loop: run all checks, if failures and iterations < max_repair_iterations: send repair message to LLM, parse corrected report, re-check. If still failing: degrade (mark claims unverified).

2. Create `src/athena/verify/repair.py`: `build_repair_message(failures)` constructs structured JSON listing each failure with issue and suggestion. `parse_repaired_report(llm_response)` parses corrected Report.

3. Create `src/athena/render/renderer.py`: `resolve_placeholders(report, tool_results)` replaces `{{tool_id.metric}}` with actual values (configurable decimal formatting). `format_report(report)` produces final report dict.

4. Create `src/athena/render/__init__.py`.

5. Create `tests/test_verifier.py`: test repair loop (violations fixed on retry), test degrade (unfixable violations marked unverified).
6. Create `tests/test_renderer.py`: test placeholder resolution, unresolvable placeholder handling.

**Files:** `src/athena/verify/verifier.py`, `src/athena/verify/repair.py`, `src/athena/render/renderer.py`, `src/athena/render/__init__.py`, `tests/test_verifier.py`, `tests/test_renderer.py`
**Accept:** Verifier runs rules, triggers repairs, degrades when needed. Renderer resolves placeholders.
**Depends:** 4.1, 0.5.

---

### Task 4.3 — Integrate verifier into orchestrator

**Do:** Update `src/athena/agent/orchestrator.py`: after draft report, call `verifier.verify(report, trace, llm_client)`. Include verification summary in RunResult. Emit SSE events for verification status.

Update `tests/test_orchestrator.py` to verify integration.

**Files:** `src/athena/agent/orchestrator.py` (modify), `tests/test_orchestrator.py` (modify)
**Accept:** End-to-end: orchestrator -> tools -> draft -> verifier -> final report. Verification summary populated.
**Depends:** 2.3, 4.2.

---

## M5 — Benchmark Complete

### Task 5.1 — Expand to 40-50 benchmark questions

**Do:**
1. Expand `benchmark/questions/questions.json` to 40-50 questions:
   - 8-10 descriptive/SQL
   - 8-10 hypothesis tests
   - 5-6 modeling
   - 5-6 leakage detection
   - 5-6 unanswerable/refusal/causal trap
   - 3-4 prompt injection
   - 3-5 multi-step
2. Add Titanic dataset as 4th benchmark dataset.
3. Ground-truth scripts for all new questions.
4. Planted-leakage variants for Adult Income and California Housing.

**Files:** `benchmark/questions/questions.json`, `benchmark/ground_truth/*.py`, `benchmark/datasets/`
**Accept:** All ground-truth scripts run. 40+ questions defined.
**Depends:** 1.5.

---

### Task 5.2 — Benchmark runner + scorer

**Do:**
1. Create `benchmark/scorer.py`: tolerance checking per ADR-10 (numeric relative/absolute, categorical exact, boolean, direction, refusal). Compare Athena output to ground truth. Compute metrics: accuracy, hallucination rate, refusal accuracy, leakage P/R, latency, tokens.

2. Create `benchmark/runner.py`: CLI `python -m benchmark.runner --systems A1,A2,B1 --repeats 3 --questions all|smoke`. For each system x question x repeat: run, score, record. Output: `benchmark/results/results.json`, `results.md`, `failure_analysis.md`.

3. Create `benchmark/baselines/b1_plain_llm.py`: B1 baseline — LLM given schema + sample rows, writes pandas code, executed in sandbox (`exec` with restricted globals).

4. Update CI smoke job to run 5 questions with `LLM_CACHE_MODE=replay`.

**Files:** `benchmark/scorer.py`, `benchmark/runner.py`, `benchmark/baselines/b1_plain_llm.py`, `.github/workflows/benchmark-smoke.yml` (modify)
**Accept:** Runner produces results table. Smoke subset runs in CI.
**Depends:** 5.1, 2.3, 4.3.

---

## M6 — API + UI

### Task 6.1 — FastAPI application + routes

**Do:**
1. `src/athena/api/main.py`: FastAPI app, CORS middleware, serve static files from `static/`, health check `GET /health`.

2. `src/athena/api/events.py`: SSE event types, serialization, `EventSourceResponse` usage.

3. `src/athena/api/routes.py`:
   - `POST /api/datasets` — upload CSV/Parquet, returns dataset ID + profile.
   - `GET /api/datasets/{id}/profile` — get profile.
   - `GET /api/demo-datasets` — list demo datasets.
   - `POST /api/sessions` — create session with dataset.
   - `POST /api/sessions/{id}/ask` — ask question (SSE stream of events).
   - `GET /api/runs/{id}` — fetch completed run (report + trace).
   - `GET /api/benchmark/results` — fetch benchmark results.

4. `src/athena/api/__init__.py`.

5. `tests/test_api.py`: test upload, profile, ask (mocked orchestrator).

**Files:** `src/athena/api/main.py`, `src/athena/api/routes.py`, `src/athena/api/events.py`, `src/athena/api/__init__.py`, `tests/test_api.py`
**Accept:** All endpoints work. SSE streaming works. Tests pass.
**Depends:** 2.3, 4.3.

---

### Task 6.2 — Initialize React frontend

**Do:**
1. In `frontend/` directory, run: `npx -y create-vite@latest ./ -- --template react-ts`.
2. `npm install`.
3. Add deps: `react-plotly.js`, `plotly.js-dist-min`, type defs.
4. Configure Vite proxy to FastAPI (port 8000).
5. Set up structure:
   ```
   frontend/src/
     main.tsx, App.tsx
     api/     (client.ts, types.ts)
     components/ (Layout, DatasetPanel, QueryInput, ReportView, EvidenceChip, VerificationBadge, ExecutionTrace, BenchmarkView, ProfileCard)
     styles/  (global.css)
   ```
6. Create TypeScript types matching backend schemas.

**Files:** `frontend/` directory
**Accept:** `npm run dev` starts. `npm run build` succeeds.
**Depends:** 0.1.

---

### Task 6.3 — Frontend: Dataset panel + profile card

**Do:**
1. `DatasetPanel.tsx`: file upload (drag-and-drop + click), demo dataset picker, calls `POST /api/datasets`.
2. `ProfileCard.tsx`: row/column counts, columns with types, missingness bars, warnings. Clean dark-theme design.

**Files:** `frontend/src/components/DatasetPanel.tsx`, `frontend/src/components/ProfileCard.tsx`, styles
**Accept:** Upload works. Profile card renders with demo data.
**Depends:** 6.2, 6.1.

---

### Task 6.4 — Frontend: Query input + report view

**Do:**
1. `QueryInput.tsx`: text input, submit, loading state, inline clarification display.
2. `ReportView.tsx`: TL;DR, findings with evidence chips, Plotly charts, caveats, recommendations, verification badge.
3. `EvidenceChip.tsx`: clickable badge, expands to show tool call details.
4. `VerificationBadge.tsx`: "12/12 verified" with green/yellow/red color, expandable details.

**Files:** `frontend/src/components/QueryInput.tsx`, `ReportView.tsx`, `EvidenceChip.tsx`, `VerificationBadge.tsx`
**Accept:** Report renders. Evidence chips expand. Badge shows correct counts.
**Depends:** 6.3.

---

### Task 6.5 — Frontend: Execution trace + SSE + assembly

**Do:**
1. `ExecutionTrace.tsx`: live-updating timeline of steps (tool name, status, runtime, expandable). Auto-scroll.
2. `api/client.ts`: SSE client using `EventSource` for `/api/sessions/{id}/ask`. Parse all event types. React hooks for state updates.
3. `BenchmarkView.tsx`: results table, filterable by system/category.
4. `App.tsx`: three-panel layout (left: dataset, center: query+report, right: trace). Wire everything.

**Files:** `frontend/src/api/client.ts`, `ExecutionTrace.tsx`, `BenchmarkView.tsx`, `App.tsx`
**Accept:** Full flow: upload -> ask -> streaming trace -> report. Benchmark tab works.
**Depends:** 6.4.

---

## M7 — MCP + Deploy + Docs

### Task 7.1 — MCP server

**Do:** Create `src/athena/mcp_server/server.py` per ADR-13:
- Wrap each tool with MCP tool decorators. stdio transport.
- Each tool creates DatasetHandle from file path argument.
- `src/athena/mcp_server/__init__.py`.
- Entry point already in `pyproject.toml` from Task 0.1.
- Create `docs/mcp-usage.md`: Claude Desktop config JSON + Python client script example.

**Files:** `src/athena/mcp_server/server.py`, `src/athena/mcp_server/__init__.py`, `docs/mcp-usage.md`
**Accept:** `athena-mcp` starts. Tools callable from Python client.
**Depends:** All tools (0.7).

---

### Task 7.2 — Dockerfile + Render deployment

**Do:**
1. `Dockerfile`: multi-stage build (Node frontend build -> Python backend). Bundle `demo_data/`. Set `DEMO_MODE=true`.
2. `render.yaml`: web service, docker env, free plan, env vars for API key and demo mode.
3. Test locally: `docker build -t athena . && docker run -p 8000:8000 athena`.

**Files:** `Dockerfile`, `render.yaml`
**Accept:** Docker image builds and serves app on port 8000.
**Depends:** 6.5, 6.1.

---

### Task 7.3 — README + AGENTS.md

**Do:**
1. `README.md`: overview, architecture diagram (Mermaid), screenshot/GIF, benchmark results table, local setup, benchmark instructions, ADR links, failure analysis, what "verified" means, live demo link.
2. `AGENTS.md`: code style (ruff), testing conventions, how to add a tool, how to add a benchmark question, commit format.

**Files:** `README.md`, `AGENTS.md`
**Accept:** README comprehensive and honest.
**Depends:** 5.2, 7.2.

---

### Task 7.4 — Demo video/GIF

**Do:** Record 30-60s demo: pick dataset -> ask question -> watch trace -> see report with verified findings, evidence, charts. Convert to GIF. Embed in README.

**Files:** `docs/demo.gif`
**Accept:** Demo shows full flow.
**Depends:** 7.2.

---

## Dependency Graph

```
M0: 0.1 -> 0.2 -> 0.4
    0.1 -> 0.3
    0.2 + 0.3 -> 0.5
    0.2 -> 0.6
    0.3 -> 0.7
    0.1 -> 0.8

M1: 0.6 + 0.7 -> 1.1
    0.1 -> 1.2
    0.6 + 1.2 -> 1.3
    0.6 + 0.7 -> 1.4
    0.1 -> 1.5

M2: 0.2 -> 2.1
    0.7 + 1.1 -> 2.2
    0.5 + 0.6 + tools + 2.1 + 2.2 -> 2.3

M3: 0.6 + 0.7 -> 3.1, 3.2, 3.4
    3.1 -> 3.3

M4: 0.3 -> 4.1
    4.1 + 0.5 -> 4.2
    2.3 + 4.2 -> 4.3

M5: 1.5 -> 5.1
    5.1 + 2.3 + 4.3 -> 5.2

M6: 2.3 + 4.3 -> 6.1
    0.1 -> 6.2
    6.2 + 6.1 -> 6.3 -> 6.4 -> 6.5

M7: all tools -> 7.1
    6.5 + 6.1 -> 7.2
    5.2 + 7.2 -> 7.3 -> 7.4
```

## Priority if Time Runs Short

**Never cut:** Verifier (M4), Benchmark (M5).
**Cut last:** Core tools (M1), Orchestrator (M2).
**Cut first:** MCP (7.1), Demo video (7.4), visual polish.
**Reduce scope:** Benchmark can start at 20 questions. UI can be simpler but must exist.
