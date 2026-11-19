# ADR-35: Handling Zero-Variance Categorical Predictors in LightGBM

## Status
Accepted

## Context
In automated machine learning pipelines, datasets frequently contain invariant columns (constant values,
e.g. `is_active=True` for all rows, or single unique categories). Passing invariant or single-category
features into LightGBM or SHAP TreeExplainer can cause matrix degeneracy, division-by-zero warnings,
or unnecessary memory bloat.

## Decision
1. In `src/athena/tools/ml.py`, automatically detect and prune features where `nunique <= 1` prior to dataset splitting.
2. Log all pruned columns in `ToolResult.warnings` with reason `"zero_variance_pruned"`.
3. Inform the SHAP explainer module of pruned features to avoid dimension mismatch in feature importance mapping.

## Consequences
- Robust model fitting without LightGBM numerical instability warnings.
- Clear audit trail in tool metadata explaining why invariant columns were dropped.
- Streamlined downstream SHAP feature attribution matrices.
