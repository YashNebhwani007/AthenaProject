# ADR-01: Report Generation Strategy

**Status:** Accepted
**Date:** 2026-10-08
**Decision:** D1 — Report generation: placeholder/reference templating vs structured claims vs post-hoc number extraction.

## Context
The LLM must produce a report where every data-derived number is traceable to a tool output. The brief's `{{t3.p_value}}` syntax implies a templating approach, but alternatives exist.

## Options

### Option A: Placeholder/Reference Templating (Recommended)
The LLM writes prose with `{{tool_id.metric_name}}` placeholders. The renderer resolves them from the tool result store.

| Dimension | Assessment |
|-----------|-----------|
| Complexity | Low — simple regex/template resolution |
| Correctness | High — numbers are always exact tool outputs, never LLM-typed |
| Verifier integration | Excellent — verifier checks that every `{{...}}` resolves to a real metric |
| Risk | Medium — LLM must learn the placeholder syntax reliably |
| Interview showcase | Good — demonstrates a novel trustworthiness mechanism |

### Option B: Structured Claims Array
The LLM returns only structured JSON claims (finding ID, claim text with no numbers, list of metric references). The renderer assembles prose from claims.

| Dimension | Assessment |
|-----------|-----------|
| Complexity | Medium — renderer must generate readable prose from structured data |
| Correctness | Very high — no opportunity for hallucinated numbers |
| Risk | High — generated prose may read unnaturally |
| Interview showcase | Good but hard to explain quickly |

### Option C: Post-hoc Number Extraction
The LLM writes free prose with literal numbers. A post-processing step extracts numbers, matches them to tool outputs, and flags mismatches.

| Dimension | Assessment |
|-----------|-----------|
| Complexity | High — NLP/regex extraction, fuzzy matching to metrics |
| Correctness | Low — extraction is error-prone, rounding creates false positives |
| Risk | High — the very thing we're trying to prevent (hallucinated numbers) is the default |
| Interview showcase | Weak — reactive rather than proactive |

## Decision
**Option A: Placeholder/Reference Templating.**

The brief already uses this syntax. It's the simplest approach that makes hallucinated numbers structurally impossible (not just detectable). The verifier becomes a completeness checker rather than an extractor.

Implementation details:
- Placeholders follow the pattern `{{tool_result_id.metric_name}}`.
- The renderer resolves them with configurable formatting (decimal places, percentage conversion).
- The verifier checks: (1) every placeholder resolves, (2) no unresolved literal numbers appear in finding text (except allowed config constants), (3) evidence arrays are consistent with placeholders used.
- If the LLM writes a literal data-derived number, the verifier flags it for repair or marks the claim unverified.

## Consequences
- The system prompt must teach the LLM the placeholder syntax with examples.
- Need a small parser for `{{...}}` resolution.
- Benchmark must include cases where the LLM fails to use placeholders (to test verifier catch rate).
