# TreeSHAP vs KernelSHAP Performance Trade-offs

## Overview
Computing Shapley values provides mathematically consistent local feature attributions rooted in
cooperative game theory. Athena's `explain_model` tool chooses the optimal SHAP explainer implementation
based on model architecture and computational constraints.

## Explainer Architecture Comparison

| Feature | TreeSHAP (`TreeExplainer`) | KernelSHAP (`KernelExplainer`) |
|---|---|---|
| **Model Compatibility** | Tree-based models (LightGBM, XGBoost, Random Forest) | Model-agnostic (Neural nets, SVMs, Ensembles) |
| **Computational Complexity** | $O(T L D^2)$ polynomial time | Exponential without aggressive background sampling |
| **Runtime for 1,000 Rows** | $\approx 45 \text{ ms}$ | $\approx 35 \text{ seconds}$ |
| **Background Data Need** | None needed (uses tree path margins) | Requires representative $k$-means background set |
| **Exactness** | Mathematically exact for tree ensembles | Approximate Monte Carlo sampling |

## Recommendations for Athena Pipelines
1. Always use `TreeExplainer` when working with Athena's native LightGBM predictive models.
2. For large evaluation sets ($N > 10,000$), calculate SHAP values on a stratified sample of 1,000
   instances to ensure response latency stays under 200ms.
