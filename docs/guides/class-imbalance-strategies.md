# Handling Class Imbalance in Tabular Predictive Pipelines

## Overview
Tabular datasets frequently exhibit severe class imbalance (e.g. churn rate of 5%, fraud rate of 0.1%).
Standard accuracy metrics are misleading in these scenarios, and default gradient boosting objectives
may produce trivial majority-class models.

## Strategies Implemented in Athena

### 1. Metric Selection
Athena's `train_model` tool evaluates imbalanced classifiers using threshold-invariant and positive-class metrics:
- **ROC AUC:** Measures ranking quality across all classification thresholds.
- **PR AUC (Average Precision):** Recommended when positive class prevalence is under 10%.
- **Macro F1 Score:** Balances minority and majority class precision and recall.

### 2. Algorithmic Rebalancing
Athena exposes `is_unbalance=True` or `scale_pos_weight` in LightGBM:
$$\text{scale\_pos\_weight} = \frac{N_{\text{negative}}}{N_{\text{positive}}}$$

When enabled:
- Minority class loss gradients are scaled proportionally during tree split computation.
- Avoids synthesizing artificial records that may distort causal relationships.

### 3. Stratified Cross-Validation
Dataset splits in `src/athena/tools/ml.py` use `StratifiedKFold` to ensure identical class distributions
across training and out-of-fold validation splits.
