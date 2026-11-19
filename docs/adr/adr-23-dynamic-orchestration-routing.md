# ADR-23: Dynamic Fast-Path vs Deep-Verification Orchestration Routing

## Status
Accepted

## Context
Simple queries (e.g., "What is the row count?", "What is the average fare?") do not require
multi-step predictive modeling, SHAP explainability, or multiple verifier repair loops.
Treating all queries uniformly leads to excessive latency and token expenditure for simple lookup tasks.

## Decision
1. Introduce query intent classification in the Orchestrator before plan execution.
2. Route queries into two analytical execution profiles:
   - **Fast-Path:** Single SQL query + light profile check, single pass through V1 grounding rule, 0 repair iterations.
   - **Deep-Verification:** Full hypothesis test recommendation, leakage audit, ML pipeline, 5-point adversarial verification loop, up to 3 repair iterations.
3. Automatically escalate to Deep-Verification if the fast-path query encounters missingness > 30% or schema ambiguity.

## Consequences
- Fast-path queries complete in < 2 seconds with minimal token consumption.
- Complex analytical queries retain exhaustive statistical checks and automated repair.
- Configurable per-session override via `Settings.force_deep_verification`.
