# SHAP Explainability & Interpretation Manual

Athena's `explain_model` tool extracts both global feature rankings and individual instance waterfall explanations.

## 1. Global Feature Importance
- **Method:** Mean absolute SHAP values: $\frac{1}{N} \sum_{i=1}^N |\phi_j^{(i)}|$.
- **Output:** Top-ranked features sorted by overall magnitude of impact on model predictions.
- **Artifact:** Generates a global bar chart saved to `data/plots/{model_id}_shap_summary.png`.

## 2. Local Sample Attribution
- **Method:** Additive feature attributions for a single instance: $\hat{f}(x) = \phi_0 + \sum_{j=1}^M \phi_j(x)$.
- **Output:** Individual feature contributions with positive (green) and negative (red) impact signs.
- **Artifact:** Generates a waterfall/horizontal contribution plot saved to `data/plots/{model_id}_shap_local_{idx}.png`.
