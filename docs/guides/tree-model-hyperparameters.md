# LightGBM Model Architecture & Cross-Validation Manual

Athena utilizes Microsoft's LightGBM framework for deterministic tabular modeling due to its
histogram-based gradient boosting speed, native categorical support, and TreeSHAP compatibility.

---

## 1. Baseline Hyperparameter Configuration
To prevent overfitting on small benchmark datasets while maintaining fast convergence:

| Parameter | Binary Classification | Continuous Regression | Rationale |
| :--- | :--- | :--- | :--- |
| `objective` | `binary` | `regression` | Task-appropriate loss formulation |
| `metric` | `auc`, `binary_logloss` | `rmse`, `mae` | Robust generalization metrics |
| `max_depth` | `5` | `6` | Shallow tree limit prevents leaf memorization |
| `num_leaves` | `31` | `31` | Controls tree complexity |
| `learning_rate`| `0.05` | `0.05` | Conservative shrinkage rate |
| `n_estimators` | `100` | `100` | Sufficient steps with early stopping |
| `min_child_samples` | `20` | `20` | Prevents isolated single-row splits |

---

## 2. Leak-Free Cross-Validation Scheme
1. **Stratified Split:** Classification tasks use 5-fold Stratified K-Fold to maintain class balance across splits.
2. **Preprocessing Isolation:** Imputation and label encoding fit strictly on the training folds.
3. **Out-of-Fold Metrics:** ROC-AUC, Precision, Recall, and F1 computed on held-out test splits only.
4. **Target Leakage Gate:** If single-feature AUC exceeds 0.95 during pre-training audit, the pipeline aborts.
