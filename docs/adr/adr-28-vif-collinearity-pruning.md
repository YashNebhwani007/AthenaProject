# ADR-28: Variance Inflation Factor (VIF) Collinearity Pruning

## Status
Accepted

## Context
High multicollinearity among predictive features distorts linear coefficients and scatters
SHAP attribution across redundant features, rendering feature importance rankings noisy and unstable.
For instance, in economic models, median rooms and median bedrooms often exhibit Pearson $r > 0.90$.

## Decision
1. Calculate the Variance Inflation Factor (VIF) for all numerical features during pipeline preprocessing.
2. Flag features with $\text{VIF} > 10.0$ as severely collinear.
3. Automatically prune the feature with the higher VIF in each collinear pair prior to fitting linear models, or group them in tree-based model SHAP cluster explanations.
4. Report detected collinear feature clusters in the `data_profile` metrics so the analyst is aware of redundancy.

## Consequences
- Stable, interpretable linear regression coefficients and reliable SHAP values.
- Faster tree model convergence and reduced memory requirements during gradient boosting.
- Prevents redundant features from artificially diluting global importance rankings.
