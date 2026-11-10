"""Secure dataset loaders for CSV and Parquet formats."""

from pathlib import Path
from typing import TYPE_CHECKING

import duckdb
import pandas as pd

from athena.config import Settings
from athena.config import settings as global_settings
from athena.logging import get_logger

if TYPE_CHECKING:
    from athena.data.registry import ColumnInfo, DatasetHandle

logger = get_logger(__name__)


def create_secure_connection(app_settings: Settings | None = None) -> duckdb.DuckDBPyConnection:
    """Create in-memory DuckDB connection hardened against external file and network access."""
    cfg = app_settings or global_settings
    conn = duckdb.connect(
        database=":memory:",
        config={
            "enable_external_access": False,
            "lock_configuration": True,
            "max_memory": cfg.duckdb_memory_limit,
        },
    )
    return conn


def _validate_file_size(file_path: Path, cfg: Settings) -> None:
    """Validate file size against configured limit."""
    size_bytes = file_path.stat().st_size
    max_bytes = cfg.effective_max_file_size_mb * 1024 * 1024
    if size_bytes > max_bytes:
        size_mb = size_bytes / (1024 * 1024)
        raise ValueError(
            f"File size ({size_mb:.2f} MB) exceeds maximum allowed limit "
            f"({cfg.effective_max_file_size_mb} MB)"
        )


def _validate_dimensions(df: pd.DataFrame, cfg: Settings) -> None:
    """Validate row and column dimensions against configured limits."""
    row_count = len(df)
    col_count = len(df.columns)

    if row_count > cfg.effective_max_rows:
        raise ValueError(
            f"Row count ({row_count:,}) exceeds maximum allowed limit ({cfg.effective_max_rows:,})"
        )

    if col_count > cfg.max_columns:
        raise ValueError(
            f"Column count ({col_count}) exceeds maximum allowed limit ({cfg.max_columns})"
        )


def _extract_column_info(
    df: pd.DataFrame,
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    sample_n: int = 5,
) -> list["ColumnInfo"]:
    """Extract ColumnInfo metadata using DuckDB pragma and sample values."""
    from athena.data.registry import ColumnInfo

    pragma_rows = conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()
    # pragma_rows: (cid, name, type, notnull, dflt_value, pk)
    pragma_map = {row[1]: (row[2], not bool(row[3])) for row in pragma_rows}

    cols: list[ColumnInfo] = []
    for col_name in df.columns:
        col_type, col_nullable = pragma_map.get(str(col_name), ("VARCHAR", True))
        series = df[col_name].dropna()
        samples = series.head(sample_n).tolist()
        # Ensure primitive types for JSON compatibility
        clean_samples = [x.item() if hasattr(x, "item") else x for x in samples]
        cols.append(
            ColumnInfo(
                name=str(col_name),
                dtype=str(col_type),
                nullable=bool(df[col_name].isnull().any()) or col_nullable,
                sample_values=clean_samples,
            )
        )
    return cols


def _load_dataframe_into_conn(
    df: pd.DataFrame,
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    dataset_id: str,
    file_path: Path,
    fmt: str,
    cfg: Settings,
) -> "DatasetHandle":
    """Register pandas DataFrame into hardened DuckDB and return DatasetHandle."""
    from athena.data.registry import DatasetHandle

    _validate_dimensions(df, cfg)

    temp_name = f"__stage_{table_name}"
    conn.register(temp_name, df)
    conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM {temp_name}")
    conn.unregister(temp_name)

    cols = _extract_column_info(df, conn, table_name, sample_n=cfg.sample_rows)

    return DatasetHandle(
        dataset_id=dataset_id,
        table_name=table_name,
        file_path=str(file_path),
        format=fmt,
        row_count=len(df),
        column_count=len(df.columns),
        columns=cols,
    )


def load_csv(
    file_path: str | Path,
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    app_settings: Settings | None = None,
    dataset_id: str = "dataset",
) -> "DatasetHandle":
    """Read CSV, enforce security and resource limits, and load into DuckDB."""
    cfg = app_settings or global_settings
    path = Path(file_path)
    _validate_file_size(path, cfg)

    df = pd.read_csv(path)
    return _load_dataframe_into_conn(
        df=df,
        conn=conn,
        table_name=table_name,
        dataset_id=dataset_id,
        file_path=path,
        fmt="csv",
        cfg=cfg,
    )


def load_parquet(
    file_path: str | Path,
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    app_settings: Settings | None = None,
    dataset_id: str = "dataset",
) -> "DatasetHandle":
    """Read Parquet, enforce security and resource limits, and load into DuckDB."""
    cfg = app_settings or global_settings
    path = Path(file_path)
    _validate_file_size(path, cfg)

    df = pd.read_parquet(path)
    return _load_dataframe_into_conn(
        df=df,
        conn=conn,
        table_name=table_name,
        dataset_id=dataset_id,
        file_path=path,
        fmt="parquet",
        cfg=cfg,
    )
