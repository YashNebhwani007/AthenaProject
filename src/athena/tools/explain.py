"""Model explainability tool using SHAP per Task 3.3."""

import pickle
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import shap
from lightgbm import LGBMClassifier, LGBMRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression

from athena.config import Settings
from athena.config import settings as global_settings
from athena.data import DatasetRegistry, default_registry
from athena.logging import get_logger
from athena.schemas import Artifact, Metric, ToolResult, ToolStatus
from athena.tools.base import register_tool, tool_fn

matplotlib.use("Agg")
logger = get_logger(__name__)


@register_tool("explain_model")
@tool_fn("explain_model")
async def explain_model(
    model_id: str,
    dataset_id: str,
    target_col: str | None = None,
    sample_index: int = 0,
    max_samples: int = 200,
    registry: DatasetRegistry | None = None,
    app_settings: Settings | None = None,
) -> ToolResult:
    """Generate SHAP global feature importances and local explanations for a model."""
    cfg = app_settings or global_settings
    reg = registry or default_registry

    # 1. Locate and load model artifact
    model_dir = Path(cfg.data_dir) / "models"
    model_path = model_dir / f"{model_id}.pkl"
    if not model_path.exists():
        direct_path = Path(model_id)
        if direct_path.exists():
            model_path = direct_path
        else:
            raise FileNotFoundError(f"Model artifact not found at {model_path}")

    with open(model_path, "rb") as f:
        pipeline = pickle.load(f)

    # 2. Extract pipeline components
    if hasattr(pipeline, "named_steps"):
        preprocessor = pipeline.named_steps.get("preprocessor")
        estimator = pipeline.named_steps.get("model", pipeline)
    else:
        preprocessor = None
        estimator = pipeline

    # 3. Fetch dataset and select feature columns
    conn = reg.get_connection(dataset_id)
    handle = reg.get(dataset_id)
    df = conn.execute(f"SELECT * FROM {handle.table_name}").fetchdf()

    if preprocessor and hasattr(preprocessor, "feature_names_in_"):
        feature_cols = list(preprocessor.feature_names_in_)
        X = df[feature_cols]
    else:
        drop_cols = [target_col] if target_col and target_col in df.columns else []
        X = df.drop(columns=drop_cols)

    # Downsample if dataset is large for efficiency
    if len(X) > max_samples:
        X_sample = X.sample(n=max_samples, random_state=cfg.random_seed)
    else:
        X_sample = X.copy()

    # 4. Transform features and determine names
    if preprocessor:
        X_trans = preprocessor.transform(X_sample)
        if hasattr(X_trans, "toarray"):
            X_trans = X_trans.toarray()
        if hasattr(preprocessor, "get_feature_names_out"):
            raw_names = preprocessor.get_feature_names_out()
            feature_names = [
                str(name).replace("num__", "").replace("cat__", "") for name in raw_names
            ]
        else:
            feature_names = [f"f_{i}" for i in range(X_trans.shape[1])]
    else:
        X_trans = X_sample.values
        feature_names = list(X_sample.columns)

    # 5. Select appropriate SHAP explainer
    if isinstance(estimator, (LGBMClassifier, LGBMRegressor)):
        explainer = shap.TreeExplainer(estimator)
        shap_explanation = explainer(X_trans)
        raw_vals = shap_explanation.values
    elif isinstance(estimator, (LogisticRegression, LinearRegression)):
        explainer = shap.LinearExplainer(estimator, X_trans)
        shap_explanation = explainer(X_trans)
        raw_vals = shap_explanation.values
    else:
        # Fallback explainer
        background = X_trans[: min(30, len(X_trans))]
        has_proba = hasattr(estimator, "predict_proba")
        pred_fn = estimator.predict_proba if has_proba else estimator.predict
        explainer = shap.Explainer(pred_fn, background)
        shap_explanation = explainer(X_trans)
        raw_vals = shap_explanation.values

    # Handle multi-class / 3D shap values (e.g., take positive class)
    if raw_vals.ndim == 3:
        vals = raw_vals[:, :, 1]
    else:
        vals = raw_vals

    # 6. Global importance: mean |SHAP|
    mean_abs_shap = np.mean(np.abs(vals), axis=0)
    top_indices = np.argsort(mean_abs_shap)[::-1]
    global_importances = [
        {"feature": feature_names[i], "importance": float(mean_abs_shap[i])}
        for i in top_indices
    ]

    # 7. Local explanation for specific sample
    safe_sample_idx = min(sample_index, len(vals) - 1)
    local_vals = vals[safe_sample_idx]
    local_importance = [
        {"feature": feature_names[i], "shap_value": float(local_vals[i])}
        for i in np.argsort(np.abs(local_vals))[::-1]
    ]

    # 8. Render and save PNG visualizations
    plot_dir = Path(cfg.data_dir) / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)

    # Plot 1: Summary Bar Chart (top 10 global features)
    top10_idx = np.argsort(mean_abs_shap)[-10:]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(
        range(len(top10_idx)),
        mean_abs_shap[top10_idx],
        align="center",
        color="#2563EB",
    )
    ax.set_yticks(range(len(top10_idx)))
    ax.set_yticklabels([feature_names[i] for i in top10_idx])
    ax.set_xlabel("Mean |SHAP Value| (Impact on Model Output)")
    ax.set_title("Global Feature Importance (SHAP)")
    plt.tight_layout()
    summary_plot_path = plot_dir / f"{model_id}_shap_summary.png"
    fig.savefig(summary_plot_path, dpi=120)
    plt.close(fig)

    # Plot 2: Local Waterfall / Instance Contribution
    local10_idx = np.argsort(np.abs(local_vals))[-10:]
    colors = ["#10B981" if local_vals[i] >= 0 else "#EF4444" for i in local10_idx]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(
        range(len(local10_idx)),
        local_vals[local10_idx],
        align="center",
        color=colors,
    )
    ax.set_yticks(range(len(local10_idx)))
    ax.set_yticklabels([feature_names[i] for i in local10_idx])
    ax.set_xlabel("SHAP Value (Contribution to Instance Output)")
    ax.set_title(f"Local Instance Explanation (Sample {safe_sample_idx})")
    plt.tight_layout()
    local_plot_path = plot_dir / f"{model_id}_shap_local_{safe_sample_idx}.png"
    fig.savefig(local_plot_path, dpi=120)
    plt.close(fig)

    # 9. Build metrics and artifacts
    top_feature = global_importances[0]["feature"] if global_importances else "none"
    top_importance = global_importances[0]["importance"] if global_importances else 0.0

    metrics = [
        Metric(name="top_feature", value=top_feature, unit=""),
        Metric(name="top_feature_importance", value=round(top_importance, 4), unit="shap_val"),
    ]
    # Add top 3 individual feature metrics for grounding
    for rank, item in enumerate(global_importances[:3], start=1):
        metrics.append(
            Metric(
                name=f"shap_rank_{rank}_{item['feature']}",
                value=round(item["importance"], 4),
                unit="shap_val",
            )
        )

    artifacts = [
        Artifact(type="plot", ref=str(summary_plot_path).replace("\\", "/")),
        Artifact(type="plot", ref=str(local_plot_path).replace("\\", "/")),
    ]

    output_payload = {
        "model_id": model_id,
        "explainer_type": explainer.__class__.__name__,
        "sample_index": safe_sample_idx,
        "global_importance": global_importances[:10],
        "local_explanation": local_importance[:10],
        "plots": [
            str(summary_plot_path).replace("\\", "/"),
            str(local_plot_path).replace("\\", "/"),
        ],
    }

    return ToolResult(
        id="",
        tool="explain_model",
        args={"model_id": model_id, "dataset_id": dataset_id},
        status=ToolStatus.ok,
        output=output_payload,
        metrics=metrics,
        artifacts=artifacts,
    )
