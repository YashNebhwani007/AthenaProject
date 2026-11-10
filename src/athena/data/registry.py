"""Dataset registry and schema metadata management."""

from pathlib import Path
from typing import Any

import duckdb
from pydantic import BaseModel, Field

from athena.config import Settings
from athena.config import settings as global_settings
from athena.data.loaders import create_secure_connection, load_csv, load_parquet
from athena.logging import get_logger

logger = get_logger(__name__)


class ColumnInfo(BaseModel):
    """Metadata describing a single dataset column."""

    name: str
    dtype: str
    nullable: bool = True
    sample_values: list[Any] = Field(default_factory=list)


class DatasetHandle(BaseModel):
    """Handle to a registered analytical dataset in Athena."""

    dataset_id: str
    table_name: str
    file_path: str
    format: str
    row_count: int
    column_count: int
    columns: list[ColumnInfo] = Field(default_factory=list)


class DatasetRegistry:
    """Manages active datasets and their secure DuckDB connections."""

    def __init__(self, app_settings: Settings | None = None) -> None:
        self.settings = app_settings or global_settings
        self._datasets: dict[str, DatasetHandle] = {}
        self._connections: dict[str, duckdb.DuckDBPyConnection] = {}

    def register(
        self,
        dataset_id: str,
        file_path: str | Path,
        table_name: str | None = None,
    ) -> DatasetHandle:
        """Load and register a CSV or Parquet file under a secure DuckDB connection."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found: {path}")

        tbl_name = table_name or f"tbl_{dataset_id.replace('-', '_')}"
        conn = create_secure_connection(self.settings)

        suffix = path.suffix.lower()
        if suffix == ".csv":
            handle = load_csv(path, conn, tbl_name, self.settings, dataset_id=dataset_id)
        elif suffix in (".parquet", ".pq"):
            handle = load_parquet(path, conn, tbl_name, self.settings, dataset_id=dataset_id)
        else:
            msg = f"Unsupported file format: {suffix}. Supported formats: .csv, .parquet"
            raise ValueError(msg)

        self._datasets[dataset_id] = handle
        self._connections[dataset_id] = conn
        logger.info(
            "dataset_registered",
            dataset_id=dataset_id,
            table=tbl_name,
            rows=handle.row_count,
            cols=handle.column_count,
        )
        return handle

    def __contains__(self, dataset_id: str) -> bool:
        """Check if dataset ID is registered."""
        return dataset_id in self._datasets

    def has(self, dataset_id: str) -> bool:
        """Check if dataset ID is registered."""
        return dataset_id in self._datasets

    def get(self, dataset_id: str) -> DatasetHandle:
        """Retrieve dataset handle by ID."""
        if dataset_id not in self._datasets:
            raise KeyError(f"Dataset ID '{dataset_id}' not found in registry")
        return self._datasets[dataset_id]

    def get_connection(self, dataset_id: str) -> duckdb.DuckDBPyConnection:
        """Retrieve active DuckDB connection for a dataset."""
        if dataset_id not in self._connections:
            raise KeyError(f"Connection for dataset ID '{dataset_id}' not found")
        return self._connections[dataset_id]

    def get_schema_summary(self, dataset_id: str) -> str:
        """Generate human-readable Markdown summary of dataset schema."""
        handle = self.get(dataset_id)
        lines = [
            (
                f"Table `{handle.table_name}` "
                f"({handle.row_count} rows, {handle.column_count} columns):"
            ),
            "| Column | Type | Nullable | Sample Values |",
            "| :--- | :--- | :--- | :--- |",
        ]
        for col in handle.columns:
            samples = ", ".join(repr(v) for v in col.sample_values[:3])
            lines.append(f"| {col.name} | {col.dtype} | {col.nullable} | {samples} |")
        return "\n".join(lines)

    def get_sample_rows(self, dataset_id: str, n: int = 5) -> list[dict[str, Any]]:
        """Fetch first n rows from the registered table."""
        handle = self.get(dataset_id)
        conn = self.get_connection(dataset_id)
        cursor = conn.execute(f"SELECT * FROM {handle.table_name} LIMIT {n}")  # noqa: S608
        col_names = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(col_names, row, strict=False)) for row in rows]

    def cleanup(self, dataset_id: str | None = None) -> None:
        """Close connections and remove datasets from memory."""
        if dataset_id is not None:
            if dataset_id in self._connections:
                self._connections[dataset_id].close()
                del self._connections[dataset_id]
            self._datasets.pop(dataset_id, None)
        else:
            for conn in self._connections.values():
                conn.close()
            self._connections.clear()
            self._datasets.clear()


default_registry = DatasetRegistry()
