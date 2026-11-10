"""Visualization tool supporting multiple chart types per Task 3.4."""

import json
import uuid
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from athena.config import Settings
from athena.config import settings as global_settings
from athena.data import DatasetRegistry, default_registry
from athena.logging import get_logger
from athena.schemas import Artifact, Metric, ToolResult, ToolStatus
from athena.tools.base import register_tool, tool_fn

matplotlib.use("Agg")
logger = get_logger(__name__)

VALID_CHART_TYPES = {
    "histogram",
    "bar",
    "box",
    "scatter",
    "correlation_heatmap",
    "shap_summary",
}


@register_tool("make_plot")
@tool_fn("make_plot")
async def make_plot(
    dataset_id: str,
    chart_type: str,
    x: str | None = None,
    y: str | None = None,
    color: str | None = None,
    title: str | None = None,
    registry: DatasetRegistry | None = None,
    app_settings: Settings | None = None,
) -> ToolResult:
    """Generate statistical visualizations (PNG export + Plotly spec) with summary."""
    cfg = app_settings or global_settings
    reg = registry or default_registry

    if chart_type not in VALID_CHART_TYPES:
        raise ValueError(
            f"Unsupported chart_type '{chart_type}'. Must be one of: {sorted(VALID_CHART_TYPES)}"
        )

    conn = reg.get_connection(dataset_id)
    handle = reg.get(dataset_id)
    df = conn.execute(f"SELECT * FROM {handle.table_name}").fetchdf()

    plot_dir = Path(cfg.data_dir) / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)
    plot_id = f"plot_{uuid.uuid4().hex[:8]}"
    png_path = plot_dir / f"{plot_id}.png"

    metrics: list[Metric] = []
    text_summary = ""
    plotly_fig = go.Figure()

    # Style presets
    has_seaborn = "seaborn-v0_8-whitegrid" in plt.style.available
    plt.style.use("seaborn-v0_8-whitegrid" if has_seaborn else "default")
    fig, ax = plt.subplots(figsize=(8, 5))

    chart_title = title or f"{chart_type.replace('_', ' ').title()} - {dataset_id}"

    if chart_type == "histogram":
        if not x or x not in df.columns:
            raise ValueError(f"Histogram requires numeric column 'x', got '{x}'")
        series = pd.to_numeric(df[x], errors="coerce").dropna()
        mean_val = float(series.mean())
        median_val = float(series.median())
        std_val = float(series.std())

        # Matplotlib PNG
        ax.hist(series, bins=30, color="#3B82F6", edgecolor="white", alpha=0.85)
        ax.axvline(mean_val, color="#EF4444", linestyle="--", label=f"Mean ({mean_val:.2f})")
        ax.axvline(median_val, color="#10B981", linestyle=":", label=f"Median ({median_val:.2f})")
        ax.set_xlabel(x)
        ax.set_ylabel("Frequency")
        ax.legend()

        # Plotly
        plotly_fig.add_trace(go.Histogram(x=series, name=x, marker_color="#3B82F6"))

        text_summary = (
            f"Distribution of {x} (N={len(series):,}): Mean is {mean_val:.2f}, "
            f"Median is {median_val:.2f}, Std is {std_val:.2f}."
        )
        metrics.extend(
            [
                Metric(name=f"{x}_mean", value=round(mean_val, 4), unit=""),
                Metric(name=f"{x}_median", value=round(median_val, 4), unit=""),
                Metric(name=f"{x}_std", value=round(std_val, 4), unit=""),
            ]
        )

    elif chart_type == "bar":
        if not x or x not in df.columns:
            raise ValueError(f"Bar chart requires category column 'x', got '{x}'")

        if y and y in df.columns:
            grouped = df.groupby(x)[y].mean().sort_values(ascending=False).head(15)
            y_label = f"Mean {y}"
        else:
            grouped = df[x].value_counts().head(15)
            y_label = "Count"

        categories = [str(idx) for idx in grouped.index]
        values = grouped.values

        ax.bar(categories, values, color="#3B82F6", edgecolor="white")
        ax.set_xlabel(x)
        ax.set_ylabel(y_label)
        ax.tick_params(axis="x", rotation=45)

        plotly_fig.add_trace(go.Bar(x=categories, y=values, marker_color="#3B82F6"))

        top_cat = categories[0]
        top_val = float(values[0])
        text_summary = (
            f"Bar chart of {x} showing top {len(categories)} categories. "
            f"Highest: '{top_cat}' with {top_val:,.2f} {y_label.lower()}."
        )
        metrics.append(Metric(name=f"top_{x}_category", value=top_cat, unit=""))
        metrics.append(Metric(name=f"top_{x}_value", value=round(top_val, 4), unit=""))

    elif chart_type == "box":
        col_to_plot = y or x
        if not col_to_plot or col_to_plot not in df.columns:
            raise ValueError("Box plot requires numeric column in 'y' (or 'x')")

        if x and y and x in df.columns and y in df.columns and x != y:
            # Grouped box plot
            groups = [group.dropna() for _, group in df.groupby(x)[y]]
            labels = [str(k) for k in df.groupby(x).groups.keys()][:10]
            ax.boxplot(groups[:10], tick_labels=labels, patch_artist=True)
            ax.set_xlabel(x)
            ax.set_ylabel(y)
            ax.tick_params(axis="x", rotation=45)

            for group_name, group_data in df.groupby(x):
                plotly_fig.add_trace(go.Box(y=group_data[y], name=str(group_name)))

            text_summary = f"Box plot of {y} grouped across {len(labels)} categories of {x}."
        else:
            series = pd.to_numeric(df[col_to_plot], errors="coerce").dropna()
            q1 = float(series.quantile(0.25))
            median_val = float(series.median())
            q3 = float(series.quantile(0.75))
            ax.boxplot(series, patch_artist=True)
            ax.set_ylabel(col_to_plot)

            plotly_fig.add_trace(go.Box(y=series, name=col_to_plot, marker_color="#3B82F6"))
            text_summary = (
                f"Box plot for {col_to_plot}: Median={median_val:.2f}, "
                f"Q1={q1:.2f}, Q3={q3:.2f}, IQR={q3 - q1:.2f}."
            )
            metrics.extend(
                [
                    Metric(name=f"{col_to_plot}_median", value=round(median_val, 4), unit=""),
                    Metric(name=f"{col_to_plot}_iqr", value=round(q3 - q1, 4), unit=""),
                ]
            )

    elif chart_type == "scatter":
        if not x or not y or x not in df.columns or y not in df.columns:
            raise ValueError(f"Scatter plot requires columns 'x' and 'y', got '{x}', '{y}'")

        sub = df[[x, y]].dropna()
        x_vals = pd.to_numeric(sub[x], errors="coerce")
        y_vals = pd.to_numeric(sub[y], errors="coerce")
        valid = ~(x_vals.isna() | y_vals.isna())
        x_vals, y_vals = x_vals[valid], y_vals[valid]

        r_corr = float(np.corrcoef(x_vals, y_vals)[0, 1]) if len(x_vals) > 1 else 0.0

        ax.scatter(x_vals, y_vals, alpha=0.6, color="#3B82F6", edgecolors="none")
        if len(x_vals) > 1:
            m, b = np.polyfit(x_vals, y_vals, 1)
            ax.plot(
                x_vals,
                m * x_vals + b,
                color="#EF4444",
                linestyle="--",
                label=f"Trend (r={r_corr:.2f})",
            )
            ax.legend()
        ax.set_xlabel(x)
        ax.set_ylabel(y)

        plotly_fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode="markers", name=f"{x} vs {y}"))

        text_summary = (
            f"Scatter plot of {x} vs {y} (N={len(x_vals):,}) with "
            f"Pearson correlation r = {r_corr:.3f}."
        )
        metrics.append(Metric(name="pearson_r", value=round(r_corr, 4), unit="corr"))

    elif chart_type == "correlation_heatmap":
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(num_cols) < 2:
            raise ValueError("Correlation heatmap requires at least 2 numeric columns")
        num_cols = num_cols[:10]
        corr_matrix = df[num_cols].corr()

        im = ax.imshow(corr_matrix, cmap="coolwarm", vmin=-1, vmax=1)
        ax.set_xticks(range(len(num_cols)))
        ax.set_yticks(range(len(num_cols)))
        ax.set_xticklabels(num_cols, rotation=45, ha="right")
        ax.set_yticklabels(num_cols)
        fig.colorbar(im, ax=ax)

        plotly_fig.add_trace(
            go.Heatmap(z=corr_matrix.values, x=num_cols, y=num_cols, colorscale="RdBu")
        )

        upper_mask = np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        upper_corr = corr_matrix.where(upper_mask)
        strongest_pair = (
            upper_corr.abs().stack().idxmax()
            if not upper_corr.empty
            else (num_cols[0], num_cols[1])
        )
        strongest_val = float(corr_matrix.loc[strongest_pair[0], strongest_pair[1]])

        text_summary = (
            f"Correlation heatmap across {len(num_cols)} variables. "
            f"Strongest is between {strongest_pair[0]} and {strongest_pair[1]} "
            f"(r = {strongest_val:.3f})."
        )
        pair_name = f"{strongest_pair[0]}__{strongest_pair[1]}"
        metrics.append(Metric(name="strongest_corr_pair", value=pair_name, unit=""))
        metrics.append(
            Metric(name="strongest_corr_val", value=round(strongest_val, 4), unit="corr")
        )

    elif chart_type == "shap_summary":
        if x and x in df.columns and y and y in df.columns:
            feat_df = df[[x, y]].dropna().sort_values(by=y, ascending=True).tail(10)
            feats = [str(val) for val in feat_df[x]]
            importances = [float(val) for val in feat_df[y]]
        else:
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()[:10]
            variances = df[num_cols].var().sort_values().tail(10)
            feats = list(variances.index)
            importances = [float(v) for v in variances.values]

        ax.barh(range(len(feats)), importances, color="#10B981")
        ax.set_yticks(range(len(feats)))
        ax.set_yticklabels(feats)
        ax.set_xlabel("Feature Importance")

        plotly_fig.add_trace(
            go.Bar(x=importances, y=feats, orientation="h", marker_color="#10B981")
        )
        text_summary = f"Feature importance summary chart showing top {len(feats)} ranked features."
        top_name = feats[-1] if feats else "none"
        metrics.append(Metric(name="top_feature", value=top_name, unit=""))

    # Save Matplotlib figure to PNG
    ax.set_title(chart_title, fontsize=12, fontweight="bold")
    plt.tight_layout()
    fig.savefig(png_path, dpi=120)
    plt.close(fig)

    plotly_fig.update_layout(title=chart_title, template="plotly_white")
    plotly_spec = json.loads(plotly_fig.to_json())

    output_payload = {
        "chart_type": chart_type,
        "title": chart_title,
        "text_summary": text_summary,
        "png_path": str(png_path).replace("\\", "/"),
        "plotly_spec": plotly_spec,
    }

    return ToolResult(
        id="",
        tool="make_plot",
        args={"dataset_id": dataset_id, "chart_type": chart_type},
        status=ToolStatus.ok,
        output=output_payload,
        metrics=metrics,
        artifacts=[Artifact(type="plot", ref=str(png_path).replace("\\", "/"))],
    )
