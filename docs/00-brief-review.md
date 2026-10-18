# Brief Review — Athena v1.0

## Purpose
This document lists ambiguities, contradictions, missing requirements, and risks found in `ATHENA_BRIEF.md`. Where a question does not block planning, an assumption is stated and carried forward. Blocking questions are called out explicitly.

---

## 1. Ambiguities

### A1 — "Numbers by reference" granularity
**Brief says:** The LLM references tool outputs via `{{t3.p_value}}` and the renderer fills them in.
**Ambiguity:** Does this mean the LLM is forbidden from writing *any* number in prose, or only numbers that originate from tool computations? For example, can it write "we used a 5-fold cross-validation" or "alpha = 0.05"?
**Assumption:** Configuration constants (alpha, k-folds, thresholds) and methodological parameters chosen by the system are allowed as literal numbers. Only data-derived numbers must be references.

### A2 — "Configurable sample rows" for data minimization
**Brief says:** The LLM sees schema, aggregate stats, tool outputs, and "(configurable) a few sample rows."
**Ambiguity:** What is the default? How is it configured? Is it per-session or global?
**Assumption:** Default = 5 rows. Configurable via a `SAMPLE_ROWS` environment variable. Global setting, overridable per-session via API parameter.

### A3 — Cleanup policy for uploads
**Brief says:** "Isolated per-session storage, cleanup policy."
**Ambiguity:** No cleanup cadence specified.
**Assumption:** Files are deleted after 24 hours of inactivity for the API; immediately on session close for the demo deployment.

### A4 — "Structured draft report" intermediate format
**Brief says:** The LLM produces a structured draft report (section 5 diagram), which the verifier processes before rendering.
**Ambiguity:** Is the "structured draft" the same JSON shape as the Report contract (section 6), or a looser intermediate format?
**Assumption:** The draft IS the Report JSON from section 6 (with `{{...}}` placeholders un-resolved). The verifier operates on this JSON, and the renderer resolves placeholders and produces the final HTML/Markdown.

### A5 — Clarifying questions behavior
**Brief says:** "If the question is ambiguous, ask one clarifying question."
**Ambiguity:** How is this surfaced in a non-interactive API call? Does the system block and wait?
**Assumption:** The API returns a `clarification_needed` event type with the question text. The UI shows it inline and allows the user to respond in the same session. If no response within 60s (or in benchmark mode), the system proceeds with a stated assumption.

### A6 — "Deterministic" tools + LLM-generated SQL
**Brief says:** Tools are "deterministic given seed" and "pure functions." But `run_sql` executes LLM-authored SQL.
**Ambiguity:** The SQL content varies per LLM call, so the tool's *output* isn't deterministic across runs — only the execution engine is.
**Assumption:** "Deterministic" for `run_sql` means: same SQL + same data = same result. The non-determinism comes from the LLM, not the tool. This is acceptable and handled by record/replay in benchmarks.

### A7 — SHAP "selected rows" for local explanations
**Brief says:** "Local explanations for selected rows."
**Ambiguity:** How are rows selected? By the LLM? By the user? Automatically?
**Assumption:** The tool auto-selects rows: the prediction closest to the decision boundary, the highest-confidence correct, and the highest-confidence incorrect (up to 3 rows). The LLM may override by specifying row indices.

### A8 — "Short doc showing MCP used from an MCP-capable client"
**Brief says:** Include a usage doc.
**Ambiguity:** Which client? Claude Desktop? A custom script? Both?
**Assumption:** Provide a doc showing usage from both (a) a simple Python MCP client script and (b) configuration for Claude Desktop (if still supported). Prioritize the Python script.

---

## 2. Contradictions

### C1 — FastAPI native SSE vs. section 12 "streamed events"
Section 12 says the API streams events (step started, tool result, report draft, verification, final). Section 14 specifies FastAPI. FastAPI ≥0.135.0 has native `EventSourceResponse`. However, the brief doesn't specify whether to use SSE, WebSockets, or chunked HTTP.
**Resolution:** Use SSE via `EventSourceResponse` — it's the simplest, works with standard `EventSource` in browsers, and matches the "streamed events" language. No WebSocket needed.

### C2 — "Simple, clear, not flashy" UI vs. portfolio impact
The brief says the UI should be "simple, clear, not flashy" (section 12), but the project is a portfolio piece where visual quality matters for interviews.
**Resolution:** "Not flashy" means no gratuitous animations or complex dashboards — but it should still be clean, modern, and well-designed. Use a professional design system (e.g., shadcn/ui) with good typography and spacing.

### C3 — react + vite + TypeScript (section 14) vs. D8 open decision
Section 14 says "frontend React + Vite + TypeScript" as a default, but D8 asks whether to use React vs. Streamlit/Gradio.
**Resolution:** This is a soft default, not a [FIXED] requirement. D8 is a genuine open decision. Resolved in ADR-08.

---

## 3. Missing Requirements

### M1 — Error handling and user feedback
No specification for how tool failures, LLM provider outages, or timeout errors are presented to the user. Need a consistent error contract.
**Impact:** Medium. An implementing agent would improvise inconsistently.
**Added:** Error responses will use a structured `ErrorEvent` in the SSE stream with `error_type`, `message`, and `recoverable` boolean.

### M2 — Rate-limit / backoff strategy details
The brief mentions rate-limit handling as an open decision (D3) but doesn't specify retry behavior, queue depth, or user-facing feedback during waits.
**Added:** Exponential backoff with jitter, max 3 retries, user sees a "waiting for LLM" status event.

### M3 — Dataset size limits (concrete numbers)
Brief says "file-size and row/column limits" but gives no numbers.
**Added defaults:** Max file size 50 MB, max 500K rows, max 500 columns. Demo deployment: 10 MB, 100K rows, 200 columns.

### M4 — Concurrency model
No mention of concurrent users/sessions. Single-user? Queue?
**Assumption:** Single-user for v1. The API accepts concurrent requests but processes one LLM-orchestrated analysis at a time (simple asyncio semaphore). This is fine for a portfolio project.

### M5 — Logging and observability
Brief mentions "structured logging" in one line. No specification of log levels, log format, or what events to log.
**Added:** Use Python `structlog` with JSON output. Log all tool calls, LLM requests (token counts, latency), verifier decisions, and errors. Log level configurable via `LOG_LEVEL` env var.

### M6 — Frontend build and deployment
No mention of how the frontend is served in production. Separate static hosting? Served by FastAPI?
**Assumption:** In development, Vite dev server proxies to FastAPI. In production, `vite build` output is served as static files by FastAPI (or co-located on Render). Single-process deployment for simplicity.

### M7 — Benchmark execution cost and time budget
40-50 questions × 3 repeats × 4 systems = 400-600 LLM calls minimum. On free-tier Groq with rate limits, this could take hours.
**Mitigation:** Record/replay cache is critical path. Run full benchmark once, cache responses. CI runs smoke subset (5 questions) with cached responses only. Document expected benchmark runtime.

---

## 4. Risks (beyond section 17)

### R1 — Groq model availability
Research shows Groq has deprecated/decommissioned models without long notice (e.g., `llama-3.3-70b-versatile` was enterprise-only at various points). Building on a single free provider is fragile.
**Mitigation:** LLM client abstraction (D3) must make provider swaps trivial. Pin to a specific model ID but make it configurable. Have a tested fallback.

### R2 — SHAP computation time
SHAP on LightGBM with >10K rows can take 30+ seconds. On free-tier deployment with limited CPU, this could timeout.
**Mitigation:** Subsample for SHAP (max 1000 rows for global, individual rows for local). Make subsample size configurable.

### R3 — DuckDB in-memory limits on free-tier
DuckDB loads data into memory. Free-tier Render instances have 512 MB RAM. A 50 MB CSV can expand to 200+ MB in memory.
**Mitigation:** Enforce file-size limits. Consider DuckDB's out-of-core mode if needed, but likely fine with 50 MB cap.

### R4 — Verifier false negatives
The verifier checks grounding (numbers match tool outputs) but cannot verify analytical correctness (e.g., wrong test chosen). Over-reliance on the "verified" badge could mislead users.
**Mitigation:** The brief already calls this out. The UI must clearly state what "verified" means. Benchmark includes cases where analysis is wrong but numbers are grounded, to demonstrate this limitation honestly.

### R5 — Scope of 40-50 benchmark questions
Writing 50 high-quality benchmark questions with ground truth scripts is a significant effort (estimate: 2-3 days of focused work). This is easy to underestimate.
**Mitigation:** Prioritize 15-20 questions in M1, expand to 40+ in M5. Ground truth scripts should be modular and share utility functions.

---

## 5. Assumptions Summary

| ID | Assumption | Section |
|-----|-----------|---------|
| A1 | Config constants (alpha, k-folds) allowed as literal numbers in LLM output | §3 |
| A2 | Default 5 sample rows, configurable via env var | §3 |
| A3 | Upload cleanup: 24h API, immediate on demo | §10 |
| A4 | Draft report = Report JSON with unresolved placeholders | §5, §6 |
| A5 | Clarification via SSE event; timeout to assumption in benchmark mode | §8 |
| A6 | "Deterministic" for run_sql means same SQL + same data = same result | §7 |
| A7 | SHAP local rows auto-selected (boundary, best correct, worst incorrect) | §7 |
| A8 | MCP usage doc: Python script + Claude Desktop config | §13 |
| M4 | Single-user concurrency, asyncio semaphore | §12 |
| M6 | Frontend served as static files by FastAPI in production | §14 |
