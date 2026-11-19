"""Tests for Athena MCP Server tool registry and invocations."""

import pytest

from athena.mcp_server.server import server


@pytest.mark.asyncio
async def test_mcp_list_tools() -> None:
    """Verify all 7 analytical tools are registered on the MCP server."""
    tools = await server.list_tools()
    tool_names = {t.name for t in tools}

    expected_tools = {
        "profile_dataset",
        "run_sql",
        "stats_test",
        "train_model",
        "explain_model",
        "predict_model",
        "leakage_check",
        "make_plot",
    }
    assert expected_tools.issubset(tool_names)


@pytest.mark.asyncio
async def test_mcp_profile_and_sql() -> None:
    """Test calling profile_dataset and run_sql via MCP server."""
    dataset_path = "benchmark/datasets/telco_churn.csv"

    # 1. Profile tool
    res = await server.call_tool("profile_dataset", {"dataset_path": dataset_path})
    assert not res.is_error
    assert len(res.content) > 0
    assert "telco_churn" in res.content[0].text

    # 2. SQL tool
    sql_res = await server.call_tool(
        "run_sql",
        {
            "dataset_path": dataset_path,
            "query": "SELECT count(*) as cnt FROM tbl_telco_churn",
        },
    )
    assert not sql_res.is_error
    assert "1000" in sql_res.content[0].text


@pytest.mark.asyncio
async def test_mcp_train_and_predict() -> None:
    """Test train_model and predict_model via MCP server."""
    dataset_path = "benchmark/datasets/telco_churn.csv"

    # Train model
    train_res = await server.call_tool(
        "train_model",
        {"dataset_path": dataset_path, "target": "churn"},
    )
    assert not train_res.is_error

    # Predict model
    pred_res = await server.call_tool(
        "predict_model",
        {
            "dataset_path": dataset_path,
            "features": {"tenure": 3, "monthly_charges": 70.0},
            "target": "churn",
        },
    )
    assert not pred_res.is_error
    assert "prediction" in pred_res.content[0].text


@pytest.mark.asyncio
async def test_mcp_call_unknown_tool_returns_error() -> None:
    """Verify calling an unregistered tool returns an error or raises an exception."""
    try:
        res = await server.call_tool("non_existent_tool_xyz", {})
        assert res.is_error or "not found" in res.content[0].text.lower()
    except Exception as exc:
        assert "not found" in str(exc).lower() or "unknown" in str(exc).lower()


@pytest.mark.asyncio
async def test_mcp_profile_missing_file_raises_tool_error() -> None:
    """Verify calling profile_dataset with a non-existent file path raises an MCP tool error."""
    with pytest.raises(Exception) as exc_info:
        await server.call_tool("profile_dataset", {"dataset_path": "non_existent_file.csv"})
    assert "profile_dataset" in str(exc_info.value) or "does not exist" in str(exc_info.value)
