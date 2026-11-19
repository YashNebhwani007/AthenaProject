# ADR-14: Predictive Inference Tool Design

**Status:** Accepted  
**Date:** 2026-11-16  
**Decision:** D14 — Out-of-sample prediction and scoring architecture.

## Context
Athena provides model training (`train_model`) and explainability (`explain_model`). However, end users and LLM agents frequently ask hypothetical questions (e.g., *"What is the survival probability for a 30-year-old female in 1st class?"*). Without a dedicated prediction tool, the agent either refused with safety disclaimers or attempted ungrounded extrapolation.

## Options Considered

### Option A: Ad-hoc Python Code Execution
Execute user feature scoring in a dynamic code interpreter sandbox.
- **Pros:** Maximum flexibility.
- **Cons:** Violates Athena's deterministic tooling boundary; non-reproducible; security risk.

### Option B: Dedicated Deterministic `predict_model` Tool (Chosen)
Implement `predict_model(features, dataset_id, model_id, target_col)`:
- Loads the persisted scikit-learn / LightGBM pipeline artifact.
- Re-uses the fitted `ColumnTransformer` (median imputation for numeric, mode/OHE for categorical).
- Aligns case-insensitive feature keys and handles missing attributes safely.
- Emits typed metrics: `prediction`, `probability`, and `probability_percent` for strict V1 verifier grounding.

## Decision
Adopt Option B. The tool integrates seamlessly into `TOOL_REGISTRY`, MCP server, and agent tool schemas.
