"""Machine learning training and evaluation tool per ADR-05."""

import pickle
import uuid
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier, LGBMRegressor
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
    root_mean_squared_error,
)
from sklearn.model_selection import KFold, StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from athena.config import Settings
from athena.config import settings as global_settings
from athena.data import DatasetRegistry, default_registry
from athena.logging import get_logger
from athena.schemas import Artifact, Metric, ToolResult, ToolStatus
from athena.tools.base import register_tool, tool_fn

logger = get_logger(__name__)


def _detect_task_type(y: pd.Series) -> str:
    """Auto-detect whether the ML task is classification or regression."""
    is_numeric = pd.api.types.is_numeric_dtype(y)
    n_unique = y.nunique()

    if not is_numeric or n_unique == 2:
        return "classification"
    if n_unique <= 20 and pd.api.types.is_integer_dtype(y):
        return "classification"
    return "regression"


def _create_preprocessor(
    num_cols: list[str],
    cat_cols: list[str],
) -> ColumnTransformer:
    """Create sklearn ColumnTransformer for numeric imputation/scaling and categorical encoding."""
    transformers = []
    if num_cols:
        num_pipeline = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]
        )
        transformers.append(("num", num_pipeline, num_cols))

    if cat_cols:
        cat_pipeline = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
            ]
        )
        transformers.append(("cat", cat_pipeline, cat_cols))

    return ColumnTransformer(transformers=transformers, remainder="drop")


@register_tool("train_model")
@tool_fn("train_model")
async def train_model(
    target_col: str,
    dataset_id: str,
    split_strategy: str = "random",
    registry: DatasetRegistry | None = None,
    app_settings: Settings | None = None,
) -> ToolResult:
    """Train baseline, linear, and gradient-boosted models, returning metrics and model artifact."""
    cfg = app_settings or global_settings
    reg = registry or default_registry
    conn = reg.get_connection(dataset_id)
    handle = reg.get(dataset_id)
    tbl = handle.table_name

    df = conn.execute(f"SELECT * FROM {tbl}").fetchdf()
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in table '{tbl}'")

    y_raw = df[target_col]
    task_type = _detect_task_type(y_raw)

    # Encode target if binary or string classification
    is_binary = False
    if task_type == "classification":
        if y_raw.dtype == object or y_raw.nunique() == 2:
            classes = sorted(y_raw.dropna().unique())
            mapping = {val: idx for idx, val in enumerate(classes)}
            y = y_raw.map(mapping)
            is_binary = len(classes) == 2
        else:
            y = y_raw
            is_binary = y.nunique() == 2
    else:
        y = y_raw.astype(float)

    # Drop target and high-cardinality row identifier columns
    drop_cols = [target_col]
    for c in df.columns:
        if c != target_col:
            if df[c].nunique() == len(df) and (
                c.lower().endswith("id") or c.lower().endswith("_key")
            ):
                drop_cols.append(c)

    X = df.drop(columns=drop_cols)
    num_cols = [c for c in X.columns if pd.api.types.is_numeric_dtype(X[c])]
    cat_cols = [c for c in X.columns if c not in num_cols]

    # Split train and test
    stratify = y if (task_type == "classification" and y.value_counts().min() >= 2) else None
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=cfg.test_size,
        random_state=cfg.random_seed,
        stratify=stratify,
    )

    # Candidate models
    if task_type == "classification":
        models = {
            "baseline": DummyClassifier(strategy="most_frequent"),
            "linear": LogisticRegression(
                random_state=cfg.random_seed,
                max_iter=1000,
                class_weight="balanced",
            ),
            "boosted": LGBMClassifier(
                random_state=cfg.random_seed,
                n_estimators=100,
                verbose=-1,
            ),
        }
        cv = StratifiedKFold(n_splits=cfg.cv_folds, shuffle=True, random_state=cfg.random_seed)
        scoring = "roc_auc" if is_binary else "f1_macro"
    else:
        models = {
            "baseline": DummyRegressor(strategy="mean"),
            "linear": LinearRegression(),
            "boosted": LGBMRegressor(
                random_state=cfg.random_seed,
                n_estimators=100,
                verbose=-1,
            ),
        }
        cv = KFold(n_splits=cfg.cv_folds, shuffle=True, random_state=cfg.random_seed)
        scoring = "neg_root_mean_squared_error"

    comparison_results: dict[str, dict[str, Any]] = {}
    fitted_pipelines: dict[str, Pipeline] = {}

    for name, estimator in models.items():
        preprocessor = _create_preprocessor(num_cols, cat_cols)
        pipe = Pipeline(
            [
                ("preprocessor", preprocessor),
                ("model", estimator),
            ]
        )

        # 5-fold cross-validation on train set
        try:
            cv_scores = cross_val_score(pipe, X_train, y_train, cv=cv, scoring=scoring)
            cv_mean = float(np.mean(cv_scores))
            cv_std = float(np.std(cv_scores))
        except Exception:
            cv_mean, cv_std = 0.0, 0.0

        # Fit on full training set
        pipe.fit(X_train, y_train)
        fitted_pipelines[name] = pipe

        # Evaluate on held-out test set
        y_pred = pipe.predict(X_test)
        metrics_dict: dict[str, float] = {}

        if task_type == "classification":
            metrics_dict["accuracy"] = float(accuracy_score(y_test, y_pred))
            metrics_dict["precision"] = float(
                precision_score(y_test, y_pred, average="macro", zero_division=0)
            )
            metrics_dict["recall"] = float(
                recall_score(y_test, y_pred, average="macro", zero_division=0)
            )
            metrics_dict["f1"] = float(f1_score(y_test, y_pred, average="macro", zero_division=0))

            if is_binary and hasattr(pipe, "predict_proba"):
                try:
                    y_prob = pipe.predict_proba(X_test)[:, 1]
                    metrics_dict["roc_auc"] = float(roc_auc_score(y_test, y_prob))
                except Exception:
                    metrics_dict["roc_auc"] = 0.5
        else:
            metrics_dict["rmse"] = float(root_mean_squared_error(y_test, y_pred))
            metrics_dict["mae"] = float(mean_absolute_error(y_test, y_pred))
            metrics_dict["r2"] = float(r2_score(y_test, y_pred))

        comparison_results[name] = {
            "cv_score_mean": round(cv_mean, 4),
            "cv_score_std": round(cv_std, 4),
            "test_metrics": {k: round(v, 4) for k, v in metrics_dict.items()},
        }

    # Best model selection
    if task_type == "classification":
        primary_key = "roc_auc" if is_binary else "f1"
        best_name = max(
            models.keys(),
            key=lambda m: comparison_results[m]["test_metrics"].get(primary_key, 0.0),
        )
    else:
        best_name = min(
            models.keys(),
            key=lambda m: comparison_results[m]["test_metrics"].get("rmse", float("inf")),
        )

    best_pipeline = fitted_pipelines[best_name]
    best_metrics = comparison_results[best_name]["test_metrics"]

    # Save model artifact to disk
    model_id = f"model_{uuid.uuid4().hex[:8]}"
    model_dir = Path(cfg.data_dir) / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / f"{model_id}.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(best_pipeline, f)

    metric_objs = [
        Metric(name=k, value=v, unit="score" if k in ("accuracy", "f1", "roc_auc", "r2") else "")
        for k, v in best_metrics.items()
    ]

    artifact_objs = [
        Artifact(type="model", ref=str(model_path).replace("\\", "/")),
    ]

    output_payload = {
        "model_id": model_id,
        "task_type": task_type,
        "target_col": target_col,
        "best_model": best_name,
        "comparison": comparison_results,
        "test_metrics": best_metrics,
        "model_artifact": str(model_path).replace("\\", "/"),
    }

    return ToolResult(
        id="",
        tool="train_model",
        args={"target_col": target_col, "dataset_id": dataset_id},
        status=ToolStatus.ok,
        output=output_payload,
        metrics=metric_objs,
        artifacts=artifact_objs,
    )
