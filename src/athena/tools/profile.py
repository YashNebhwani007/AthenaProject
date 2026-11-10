"""Dataset profiling tool."""

import re
from typing import Any

from athena.data import DatasetRegistry, default_registry
from athena.logging import get_logger
from athena.schemas import Metric, ToolResult, ToolStatus
from athena.tools.base import register_tool, tool_fn

logger = get_logger(__name__)

TARGET_NAME_PATTERNS = [
    r"^churn$",
    r"^target$",
    r"^label$",
    r"^class$",
    r"^status$",
    r"^converted$",
    r"^outcome$",
    r"^is_.*",
    r".*_churn$",
]


def _is_suspected_target(col_name: str, cardinality: int) -> bool:
    """Check if column name or distribution indicates a predictive target."""
    lower = col_name.lower()
    for pattern in TARGET_NAME_PATTERNS:
        if re.match(pattern, lower) and cardinality <= 20:
            return True
    return False


def _is_suspected_id(col_name: str, cardinality: int, row_count: int) -> bool:
    """Check if column is a unique record or primary key identifier."""
    if row_count <= 0:
        return False
    lower = col_name.lower()
    is_unique = cardinality == row_count
    has_id_name = (
        lower.endswith("_id")
        or lower.endswith("id")
        or lower.endswith("_key")
        or lower == "id"
        or "uuid" in lower
    )
    return is_unique and has_id_name


@register_tool("profile")
@tool_fn("profile")
async def profile_dataset(
    dataset_id: str,
    registry: DatasetRegistry | None = None,
) -> ToolResult:
    """Profile an analytical dataset to extract statistics and quality warnings."""
    reg = registry or default_registry
    handle = reg.get(dataset_id)
    conn = reg.get_connection(dataset_id)
    tbl = handle.table_name

    row_count_res = conn.execute(f"SELECT count(*) FROM {tbl}").fetchone()
    row_count = int(row_count_res[0]) if row_count_res else 0

    col_count = handle.column_count

    # Calculate duplicate rows
    if row_count > 0:
        q_distinct = f"SELECT count(*) FROM (SELECT DISTINCT * FROM {tbl})"
        distinct_res = conn.execute(q_distinct).fetchone()
        distinct_count = int(distinct_res[0]) if distinct_res else 0
        duplicate_rows = max(0, row_count - distinct_count)
    else:
        duplicate_rows = 0

    col_stats: dict[str, dict[str, Any]] = {}
    constant_columns: list[str] = []
    suspected_ids: list[str] = []
    suspected_targets: list[str] = []
    high_missingness_cols: list[str] = []
    warnings: list[str] = []

    # Profile each column
    for col in handle.columns:
        cname = col.name
        # Escape column name for SQL identifier safety
        esc_cname = f'"{cname}"'

        # Null count and distinct count
        q_null = f"SELECT count(*) - count({esc_cname}), count(DISTINCT {esc_cname}) FROM {tbl}"
        null_res = conn.execute(q_null).fetchone()
        null_count = int(null_res[0]) if null_res else 0
        cardinality = int(null_res[1]) if null_res else 0
        null_pct = round(null_count / row_count, 4) if row_count > 0 else 0.0

        is_numeric = any(
            t in col.dtype.upper()
            for t in ("INT", "BIGINT", "DOUBLE", "FLOAT", "REAL", "DECIMAL", "NUMERIC", "HUGEINT")
        )

        stat_entry: dict[str, Any] = {
            "dtype": col.dtype,
            "null_count": null_count,
            "null_pct": null_pct,
            "cardinality": cardinality,
            "is_numeric": is_numeric,
        }

        if is_numeric and cardinality > 0:
            q_num = (
                f"SELECT min({esc_cname}), max({esc_cname}), avg({esc_cname}), "
                f"stddev({esc_cname}), quantile_cont({esc_cname}, 0.25), "
                f"quantile_cont({esc_cname}, 0.5), quantile_cont({esc_cname}, 0.75) FROM {tbl}"
            )
            num_res = conn.execute(q_num).fetchone()
            if num_res:
                stat_entry["min"] = num_res[0]
                stat_entry["max"] = num_res[1]
                stat_entry["mean"] = round(num_res[2], 4) if num_res[2] is not None else None
                stat_entry["std"] = round(num_res[3], 4) if num_res[3] is not None else None
                stat_entry["q25"] = num_res[4]
                stat_entry["median"] = num_res[5]
                stat_entry["q75"] = num_res[6]
        else:
            # Categorical distribution
            q_cat = (
                f"SELECT {esc_cname}, count(*) as cnt FROM {tbl} "
                f"WHERE {esc_cname} IS NOT NULL GROUP BY {esc_cname} ORDER BY cnt DESC LIMIT 5"
            )
            cat_rows = conn.execute(q_cat).fetchall()
            stat_entry["top_categories"] = [
                {"value": str(r[0]), "count": int(r[1])} for r in cat_rows
            ]

        # Quality warnings and heuristic detection
        if null_pct > 0.30:
            high_missingness_cols.append(cname)
            warnings.append(f"Column '{cname}' has high missingness ({null_pct:.1%})")

        if cardinality <= 1:
            constant_columns.append(cname)
            warnings.append(f"Column '{cname}' is constant (zero variance)")

        if not is_numeric and cardinality > 100:
            warnings.append(f"Column '{cname}' has high cardinality ({cardinality} unique values)")

        if _is_suspected_id(cname, cardinality, row_count):
            suspected_ids.append(cname)

        if _is_suspected_target(cname, cardinality):
            suspected_targets.append(cname)

        col_stats[cname] = stat_entry

    output_payload = {
        "dataset_id": dataset_id,
        "table_name": tbl,
        "row_count": row_count,
        "column_count": col_count,
        "duplicate_rows": duplicate_rows,
        "columns": col_stats,
        "constant_columns": constant_columns,
        "suspected_ids": suspected_ids,
        "suspected_targets": suspected_targets,
        "high_missingness_columns": high_missingness_cols,
        "quality_warnings": warnings,
    }

    metrics = [
        Metric(name="row_count", value=row_count, unit="rows"),
        Metric(name="column_count", value=col_count, unit="columns"),
        Metric(name="duplicate_rows", value=duplicate_rows, unit="rows"),
        Metric(
            name="columns_with_high_missingness",
            value=len(high_missingness_cols),
            unit="columns",
        ),
    ]

    return ToolResult(
        id="",
        tool="profile",
        args={"dataset_id": dataset_id},
        status=ToolStatus.ok,
        output=output_payload,
        metrics=metrics,
        warnings=warnings,
    )
