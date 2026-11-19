"""Tests for system prompt, tool schemas, and context message builder."""

import json

from athena.agent.prompts import (
    SYSTEM_PROMPT,
    build_context_message,
    build_tool_schemas,
    validate_report_json_schema,
)
from athena.data.registry import ColumnInfo, DatasetHandle
from athena.schemas import ToolResult, ToolStatus


def test_system_prompt_comprehensiveness():
    """Verify SYSTEM_PROMPT contains all mandated operational rules."""
    assert "NO INVENTED NUMBERS" in SYSTEM_PROMPT
    assert "UNTRUSTED DATA" in SYSTEM_PROMPT
    assert "REFUSAL PROTOCOL" in SYSTEM_PROMPT
    assert "CORRELATION VS CAUSATION" in SYSTEM_PROMPT
    assert "findings" in SYSTEM_PROMPT
    assert "evidence" in SYSTEM_PROMPT


def test_tool_schemas_valid_json():
    """Verify tool schemas are valid JSON and contain core analytical tools."""
    schemas = build_tool_schemas()
    serialized = json.dumps(schemas)
    assert serialized is not None

    tool_names = [t["function"]["name"] for t in schemas]
    assert "run_sql" in tool_names
    assert "profile" in tool_names
    assert "recommend_test" in tool_names
    assert "stats_test" in tool_names


def test_build_context_message():
    """Verify build_context_message incorporates schema and profiling observations."""
    handle = DatasetHandle(
        dataset_id="test_ds",
        table_name="tbl_test",
        file_path="data/test.csv",
        format="csv",
        row_count=500,
        column_count=2,
        columns=[
            ColumnInfo(name="id", dtype="INTEGER", sample_values=[1, 2, 3]),
            ColumnInfo(name="churn", dtype="INTEGER", sample_values=[0, 1, 0]),
        ],
    )

    profile_res = ToolResult(
        id="t1",
        tool="profile",
        status=ToolStatus.ok,
        output={
            "quality_warnings": ["Column 'id' is unique."],
            "suspected_targets": ["churn"],
        },
    )

    msg = build_context_message(handle, profile_res)
    assert "test_ds" in msg
    assert "tbl_test" in msg
    assert "500" in msg
    assert "Column 'id' is unique." in msg
    assert "churn" in msg


def test_validate_report_json_schema():
    """Verify validate_report_json_schema validates valid Report dictionaries."""
    data = {
        "question": "What is the churn rate?",
        "answerable": True,
        "tldr": "Overall churn is 26.5%.",
        "findings": [
            {
                "id": "f1",
                "text": "Churn is 26.5%",
                "claim_type": "descriptive",
                "evidence": [{"tool_result_id": "t1", "metric": "churn_rate"}],
            }
        ],
        "caveats": ["Data from 2024"],
        "recommendations": [],
    }
    report = validate_report_json_schema(data)
    assert report.question == "What is the churn rate?"
    assert report.findings[0].id == "f1"


def test_build_context_message_with_many_columns():
    """Verify build_context_message handles datasets with many columns gracefully."""
    columns = [
        ColumnInfo(name=f"col_{i}", dtype="DOUBLE", sample_values=[i * 1.1])
        for i in range(25)
    ]
    handle = DatasetHandle(
        dataset_id="wide_ds",
        table_name="tbl_wide",
        file_path="data/wide.csv",
        format="csv",
        row_count=1000,
        column_count=25,
        columns=columns,
    )
    profile_res = ToolResult(
        id="t1",
        tool="profile",
        status=ToolStatus.ok,
        output={"quality_warnings": [], "suspected_targets": []},
    )
    msg = build_context_message(handle, profile_res)
    assert "wide_ds" in msg
    assert "col_0" in msg
    assert "col_24" in msg


def test_build_context_message_with_special_characters():
    """Verify build_context_message safely handles column names with special symbols."""
    columns = [
        ColumnInfo(
            name="col/with%special&chars", dtype="VARCHAR", sample_values=["a'b", 'c"d']
        ),
    ]
    handle = DatasetHandle(
        dataset_id="special_ds",
        table_name="tbl_special",
        file_path="data/special.csv",
        format="csv",
        row_count=10,
        column_count=1,
        columns=columns,
    )
    profile_res = ToolResult(
        id="t1",
        tool="profile",
        status=ToolStatus.ok,
        output={
            "quality_warnings": ["Warning with 'single' and \"double\" quotes."],
            "suspected_targets": [],
        },
    )
    msg = build_context_message(handle, profile_res)
    assert "col/with%special&chars" in msg
    assert "tbl_special" in msg
    assert 'Warning with \'single\' and "double" quotes.' in msg
