"""SQL execution tool running validated queries against hardened DuckDB connections."""

import asyncio
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import sqlglot

from athena.config import Settings
from athena.config import settings as global_settings
from athena.data import DatasetRegistry, default_registry
from athena.logging import get_logger
from athena.schemas import Metric, ToolResult, ToolStatus
from athena.tools.base import register_tool, tool_fn
from athena.tools.sql_validator import validate_sql

logger = get_logger(__name__)


def _clean_val(v: Any) -> Any:
    """Convert DuckDB returned types to standard JSON-serializable primitives."""
    if v is None:
        return None
    if hasattr(v, "item"):
        return v.item()
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    return v


@register_tool("run_sql")
@tool_fn("run_sql")
async def run_sql(
    query: str,
    dataset_id: str,
    max_rows: int | None = None,
    registry: DatasetRegistry | None = None,
    app_settings: Settings | None = None,
) -> ToolResult:
    """Execute a validated read-only SQL query on the dataset's secure DuckDB connection."""
    cfg = app_settings or global_settings
    reg = registry or default_registry

    # 1. AST Validation
    validation = validate_sql(query)
    if not validation.is_valid:
        raise ValueError(f"SQL validation rejected query: {validation.error}")

    sanitized = validation.sanitized_sql or query.strip()
    effective_limit = min(max_rows or cfg.sql_row_limit, cfg.sql_row_limit)

    # 2. Inject or cap LIMIT
    if not validation.has_limit:
        parsed = sqlglot.parse_one(sanitized, dialect="duckdb")
        executable_sql = parsed.limit(effective_limit).sql(dialect="duckdb")
    else:
        # Cap limit if requested limit exceeds global max limit
        if validation.limit_value is not None and validation.limit_value > cfg.sql_row_limit:
            parsed = sqlglot.parse_one(sanitized, dialect="duckdb")
            executable_sql = parsed.limit(cfg.sql_row_limit).sql(dialect="duckdb")
        else:
            executable_sql = sanitized

    # 3. Fetch connection
    conn = reg.get_connection(dataset_id)

    # 4. Execute with timeout
    def _execute() -> tuple[list[str], list[list[Any]]]:
        cursor = conn.execute(executable_sql)
        cols = [desc[0] for desc in cursor.description] if cursor.description else []
        raw_rows = cursor.fetchall()
        cleaned_rows = [[_clean_val(col) for col in row] for row in raw_rows]
        return cols, cleaned_rows

    try:
        columns, rows = await asyncio.wait_for(
            asyncio.to_thread(_execute),
            timeout=float(cfg.sql_timeout_seconds),
        )
    except TimeoutError:
        raise TimeoutError(
            f"SQL query execution timed out after {cfg.sql_timeout_seconds} seconds"
        ) from None

    total_rows = len(rows)
    truncated = total_rows >= effective_limit

    output_payload = {
        "columns": columns,
        "rows": rows,
        "total_rows": total_rows,
        "truncated": truncated,
        "query": executable_sql,
    }

    metrics = [
        Metric(name="total_rows", value=total_rows, unit="rows"),
        Metric(name="columns_returned", value=len(columns), unit="columns"),
    ]

    return ToolResult(
        id="",
        tool="run_sql",
        args={"query": query, "dataset_id": dataset_id},
        status=ToolStatus.ok,
        output=output_payload,
        metrics=metrics,
    )
