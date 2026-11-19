# ADR-32: LLM Temperature and Top-p Sampling Policies for Analytical Determinism

## Status
Accepted

## Context
Analytical reasoning and tool invocation require deterministic output from the LLM orchestrator.
Random variations in generated SQL queries, filter conditions, or statistical parameters introduce
flakiness into automated benchmark evaluations and production analytical pipelines.
Conversely, final executive narrative synthesis benefits from subtle stylistic flexibility.

## Decision
1. For tool selection, SQL generation, and statistical planning stages, set `temperature=0.0`
   and `top_p=1.0` across all model providers (Gemini, Claude, OpenAI).
2. For executive summary generation and finding synthesis, use `temperature=0.2` to enable fluent
   natural language without hallucinating numerical claims.
3. For verification passes (V1-V6 rule execution), enforce strict `temperature=0.0`.

## Consequences
- 100% reproducible execution plans across identical benchmark runs.
- Eliminates non-deterministic tool parameter generation bugs.
- Maintains professional, cohesive narrative report styling.
