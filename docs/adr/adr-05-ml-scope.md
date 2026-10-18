# ADR-05: ML Tool Scope

**Status:** Accepted
**Date:** 2026-10-08
**Decision:** D5 — ML tool scope: fixed model set vs light AutoML; handling of imbalance, missing values, categoricals.

## Context
The `train_model` tool must handle classification and regression. The brief specifies: fixed seed, explicit split, baseline model, cross-validation, held-out metrics only, class-imbalance handling, a linear model + gradient-boosted model.

## Options

### Option A: Fixed Model Set with Preprocessing Pipeline (Recommended)
Two models (LogisticRegression/LinearRegression + LightGBM), with a standardized sklearn Pipeline that handles preprocessing.

| Dimension | Assessment |
|-----------|-----------|
| Complexity | Medium — must build preprocessing pipeline, but well-understood |
| Reproducibility | Excellent — fixed models, fixed seeds, deterministic pipeline |
| Scope creep risk | Low — no model search or tuning |
| Interview showcase | Strong — shows solid ML engineering fundamentals |

### Option B: Light AutoML (e.g., FLAML or auto-sklearn)
Use a lightweight AutoML library to search a small model space.

| Dimension | Assessment |
|-----------|-----------|
| Complexity | Low to set up, high to control (seeds, reproducibility, timeout) |
| Reproducibility | Risky — AutoML search is inherently non-deterministic across runs |
| Scope creep risk | High — debugging AutoML failures is time-consuming |
| Interview showcase | Medium — "I used AutoML" is less impressive than "I built the pipeline" |

### Option C: Fixed Set + Optional Hyperparameter Search
Fixed models but with a small grid search for the boosted model.

| Dimension | Assessment |
|-----------|-----------|
| Complexity | Medium-high — adds tuning logic, CV for tuning vs evaluation |
| Reproducibility | Good if grid is fixed |
| Risk | Medium — adds time; may over-optimize on small datasets |

## Decision
**Option A: Fixed Model Set with Preprocessing Pipeline.**

Implementation:

### Models
| Task | Baseline | Simple | Boosted |
|------|----------|--------|---------|
| Classification | `DummyClassifier(strategy='most_frequent')` | `LogisticRegression(random_state=SEED, max_iter=1000)` | `LGBMClassifier(random_state=SEED, n_estimators=200, verbose=-1)` |
| Regression | `DummyRegressor(strategy='mean')` | `LinearRegression()` | `LGBMRegressor(random_state=SEED, n_estimators=200, verbose=-1)` |

### Preprocessing Pipeline (sklearn Pipeline)
1. **Column classification:** Detect numeric vs categorical columns (by dtype + cardinality heuristic).
2. **Missing values:** `SimpleImputer(strategy='median')` for numeric, `SimpleImputer(strategy='most_frequent')` for categorical.
3. **Categorical encoding:** `OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)` for LightGBM; `OneHotEncoder(handle_unknown='ignore', max_categories=20)` for linear models.
4. **Scaling:** `StandardScaler()` for linear models only.
5. **Class imbalance:** `class_weight='balanced'` for LogisticRegression; `is_unbalanced=True` for LightGBM. Report imbalance ratio in output.

### Split Strategy
- Default: `train_test_split(test_size=0.2, random_state=SEED, stratify=y)` for classification.
- Cross-validation: 5-fold `StratifiedKFold` for classification, `KFold` for regression, on training set only.
- The tool accepts a `split_strategy` parameter: `random` (default), `temporal` (if a date column is specified), `group` (if a group column is specified).

### Metrics Reported
| Task | Metrics |
|------|---------|
| Classification | accuracy, precision, recall, f1 (macro + per-class), ROC-AUC (if binary), confusion matrix |
| Regression | RMSE, MAE, R², MAPE |

All metrics reported on held-out test set. Cross-validation metrics reported as mean ± std.

### Output
- Model artifact stored by ID (pickle in session temp dir).
- `ToolResult.metrics` contains all metrics as addressable values.
- `ToolResult.output` contains confusion matrix, feature importance (from model), and comparison table (baseline vs simple vs boosted).

## Consequences
- No hyperparameter tuning — the models are fixed. This is a deliberate simplification.
- LightGBM handles categoricals natively, but we use a pipeline for consistency and to support linear models.
- Model artifacts are session-scoped and cleaned up with the session.
