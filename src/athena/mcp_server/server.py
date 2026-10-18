"""Athena MCP Server implementation per ADR-13 and Task 7.1.

Exposes Athena's analytical and verification tools over standard Model Context
Protocol (MCP) stdio transport for direct integration with Claude Desktop, Cursor,
and MCP clients.
"""

from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer

from athena.data import default_registry
from athena.data.registry import DatasetHandle
from athena.tools.explain import explain_model
from athena.tools.leakage import check_leakage
from athena.tools.ml import train_model
from athena.tools.profile import profile_dataset
from athena.tools.sql import run_sql
from athena.tools.stats import stats_test
from athena.tools.viz import make_plot

server = MCPServer("athena-tools")


def _get_or_register_handle(dataset_path: str) -> DatasetHandle:
    """Retrieve or register dataset from path and return its handle."""
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file does not exist: {dataset_path}")

    dataset_id = path.stem.replace(" ", "_")
    if dataset_id not in default_registry:
        handle = default_registry.register(dataset_id=dataset_id, file_path=path)
    else:
        handle = default_registry.get(dataset_id)

    return handle


@server.tool(name="profile_dataset")
async def mcp_profile_dataset(dataset_path: str) -> dict[str, Any]:
    """Profile a dataset: column dtypes, missingness, unique counts, and data quality warnings.

    Args:
        dataset_path: Path to the CSV or Parquet file.
    """
    handle = _get_or_register_handle(dataset_path)
    res = await profile_dataset(dataset_id=handle.dataset_id)
    return res.model_dump(mode="json")


@server.tool(name="run_sql")
async def mcp_run_sql(dataset_path: str, query: str) -> dict[str, Any]:
    """Execute a validated, read-only SQL query against the dataset table in DuckDB.

    Args:
        dataset_path: Path to the dataset file.
        query: SQL SELECT query referencing the dataset table.
    """
    handle = _get_or_register_handle(dataset_path)
    res = await run_sql(query=query, dataset_id=handle.dataset_id)
    return res.model_dump(mode="json")


@server.tool(name="stats_test")
async def mcp_stats_test(
    dataset_path: str,
    test_name: str,
    var1: str,
    var2: str,
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Run a formal hypothesis test (t-test, Mann-Whitney, ANOVA, Kruskal, Chi-squared, etc.).

    Args:
        dataset_path: Path to the dataset file.
        test_name: Name of statistical test.
        var1: First variable or grouping column name.
        var2: Second variable or value column name.
        alpha: Significance threshold (default 0.05).
    """
    handle = _get_or_register_handle(dataset_path)
    res = await stats_test(
        test_name=test_name,
        dataset_id=handle.dataset_id,
        var1=var1,
        var2=var2,
        alpha=alpha,
    )
    return res.model_dump(mode="json")


@server.tool(name="train_model")
async def mcp_train_model(
    dataset_path: str,
    target: str,
    split_strategy: str = "random",
) -> dict[str, Any]:
    """Train baseline, linear, and gradient-boosted models with leak-free preprocessing.

    Args:
        dataset_path: Path to the dataset file.
        target: Target column to predict.
        split_strategy: 'random' or 'temporal' (default 'random').
    """
    handle = _get_or_register_handle(dataset_path)
    res = await train_model(
        target_col=target,
        dataset_id=handle.dataset_id,
        split_strategy=split_strategy,
    )
    return res.model_dump(mode="json")


@server.tool(name="explain_model")
async def mcp_explain_model(
    dataset_path: str,
    model_id: str,
    target: str | None = None,
    instance_idx: int = 0,
) -> dict[str, Any]:
    """Generate SHAP explanations (TreeExplainer or LinearExplainer) for global and local insights.

    Args:
        dataset_path: Path to the dataset file.
        model_id: Model ID generated during train_model.
        target: Target column name.
        instance_idx: Index of row to explain locally.
    """
    handle = _get_or_register_handle(dataset_path)
    res = await explain_model(
        model_id=model_id,
        dataset_id=handle.dataset_id,
        target_col=target,
        sample_index=instance_idx,
    )
    return res.model_dump(mode="json")


@server.tool(name="leakage_check")
async def mcp_leakage_check(
    dataset_path: str,
    target: str,
) -> dict[str, Any]:
    """Audit dataset for target leakage, IDs, train/test duplicates, and high-correlation leaks.

    Args:
        dataset_path: Path to the dataset file.
        target: Target column name.
    """
    handle = _get_or_register_handle(dataset_path)
    res = await check_leakage(target_col=target, dataset_id=handle.dataset_id)
    return res.model_dump(mode="json")


@server.tool(name="make_plot")
async def mcp_make_plot(
    dataset_path: str,
    plot_type: str,
    x: str | None = None,
    y: str | None = None,
    color: str | None = None,
    title: str | None = None,
) -> dict[str, Any]:
    """Generate interactive Plotly and static PNG analytical visualizations.

    Args:
        dataset_path: Path to the dataset file.
        plot_type: 'histogram', 'scatter', 'bar', 'box', or 'correlation_heatmap'.
        x: Column for x-axis.
        y: Optional column for y-axis.
        color: Optional grouping column.
        title: Optional plot title.
    """
    handle = _get_or_register_handle(dataset_path)
    res = await make_plot(
        dataset_id=handle.dataset_id,
        chart_type=plot_type,
        x=x,
        y=y,
        color=color,
        title=title,
    )
    return res.model_dump(mode="json")


def main() -> None:
    """CLI Entry point for athena-mcp console script."""
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
