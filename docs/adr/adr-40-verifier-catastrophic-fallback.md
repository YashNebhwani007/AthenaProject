# ADR-40: Fallback Strategy for Catastrophic Verifier Rejection Loops

## Status
Accepted

## Context
Athena executes an automated self-repair loop when the Verifier rejects an analytical report
(e.g., due to V2 correlation direction mismatch, V4 uncited recommendations, or V1 missing metrics).
In rare cases where an LLM repeatedly fails after `max_retries=3`, the orchestrator must avoid infinite
loops while still delivering an honest, safe response.

## Decision
1. Cap self-repair attempts strictly at 3 cycles.
2. If repair attempts are exhausted without passing verifier checks:
   - Output the raw deterministic tool results (SQL tables, statistical values, SHAP plots) directly.
   - Attach an unambiguous executive warning flag explaining that automated narrative synthesis
     failed verifier audit checks and requires human review.
   - Explicitly enumerate the remaining verifier violations in the report header.

## Consequences
- Guaranteed termination of analytical orchestrator runs.
- Absolute prevention of unverified or hallucinated claims escaping to stakeholders.
- Preserves raw quantitative findings even when narrative synthesis encounters formatting errors.
