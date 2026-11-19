"""Command Line Interface (CLI) for Athena Autonomous Data Science Agent."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from athena.data.registry import DatasetRegistry
from athena.tools.leakage import check_leakage
from athena.tools.profile import profile_dataset
from athena.tools.sql import run_sql


def create_parser() -> argparse.ArgumentParser:
    """Create top-level argument parser for the Athena CLI."""
    parser = argparse.ArgumentParser(
        prog="athena",
        description="Athena — Autonomous Data Science & Decision Intelligence CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: profile
    p_profile = subparsers.add_parser("profile", help="Generate profile for a dataset file")
    p_profile.add_argument("file", type=str, help="Path to CSV or Parquet file")
    p_profile.add_argument(
        "--json", action="store_true", help="Output raw profile JSON instead of summary"
    )

    # Command: query
    p_query = subparsers.add_parser("query", help="Execute read-only SQL query on a dataset")
    p_query.add_argument("file", type=str, help="Path to CSV or Parquet file")
    p_query.add_argument("--sql", type=str, required=True, help="SQL query to execute")
    p_query.add_argument("--limit", type=int, default=50, help="Max rows to return")

    # Command: audit-leakage
    p_audit = subparsers.add_parser("audit-leakage", help="Audit dataset for target leakage")
    p_audit.add_argument("file", type=str, help="Path to CSV or Parquet file")
    p_audit.add_argument("--target", type=str, required=True, help="Target feature name")

    return parser


async def run_profile(file_path: str, as_json: bool = False) -> int:
    """Profile a dataset and print summary results."""
    path = Path(file_path).resolve()
    if not path.exists():
        sys.stderr.write(f"Error: Dataset file '{path}' not found.\n")
        return 1

    registry = DatasetRegistry()
    ds_id = "cli_ds"
    registry.register(dataset_id=ds_id, file_path=path)

    res = await profile_dataset(dataset_id=ds_id, registry=registry)
    if as_json:
        print(json.dumps(res.output, indent=2))
    else:
        out = res.output
        print(f"Dataset: {path.name}")
        print(f"Shape: {out.get('row_count', 0)} rows x {out.get('column_count', 0)} columns")
        columns = out.get("columns", {})
        print("\nColumns:")
        for col_name, stats in columns.items():
            dtype = stats.get("dtype", "unknown")
            null_pct = stats.get("null_percent", 0.0)
            print(f"  - {col_name} ({dtype}): {null_pct:.1f}% null")

    return 0


async def run_query(file_path: str, sql: str, limit: int = 50) -> int:
    """Execute SQL query against dataset file."""
    path = Path(file_path).resolve()
    if not path.exists():
        sys.stderr.write(f"Error: Dataset file '{path}' not found.\n")
        return 1

    registry = DatasetRegistry()
    ds_id = "cli_ds"
    handle = registry.register(dataset_id=ds_id, file_path=path)

    # Allow query to use table name or generic placeholder
    adjusted_sql = sql.replace("data", handle.table_name)
    res = await run_sql(query=adjusted_sql, dataset_id=ds_id, max_rows=limit, registry=registry)

    if res.warnings:
        for w in res.warnings:
            sys.stderr.write(f"Warning: {w}\n")

    out = res.output
    cols = out.get("columns", [])
    rows = out.get("rows", [])

    print("\t".join(cols))
    for r in rows:
        print("\t".join(str(cell) for cell in r))

    print(f"\n({out.get('total_rows', len(rows))} rows returned)")
    return 0 if res.status.value == "ok" else 1


async def run_audit_leakage(file_path: str, target: str) -> int:
    """Audit dataset for target leakage risks across 6 heuristic checks."""
    path = Path(file_path).resolve()
    if not path.exists():
        sys.stderr.write(f"Error: Dataset file '{path}' not found.\n")
        return 1

    registry = DatasetRegistry()
    ds_id = "cli_ds"
    registry.register(dataset_id=ds_id, file_path=path)

    res = await check_leakage(target_col=target, dataset_id=ds_id, registry=registry)
    out = res.output

    print(f"Leakage Audit Report: {path.name} (target='{target}')")
    print(f"Has Leakage: {'YES' if out.get('has_leakage') else 'NO'}")
    print(f"Max Severity: {out.get('max_severity', 'none').upper()}")

    findings = out.get("findings", [])
    if findings:
        print("\nFindings:")
        for f in findings:
            sev = f.get("severity", "none").upper()
            col = f.get("column", "all")
            print(f"  [{sev}] {col}: {f.get('detail')}")
    else:
        print("\nNo leakage risks detected.")

    return 0 if res.status.value == "ok" else 1


def main(args: list[str] | None = None) -> None:
    """CLI execution entrypoint."""
    parser = create_parser()
    parsed = parser.parse_args(args)

    if parsed.command == "profile":
        exit_code = asyncio.run(run_profile(parsed.file, as_json=parsed.json))
        sys.exit(exit_code)
    elif parsed.command == "query":
        exit_code = asyncio.run(run_query(parsed.file, sql=parsed.sql, limit=parsed.limit))
        sys.exit(exit_code)
    elif parsed.command == "audit-leakage":
        exit_code = asyncio.run(run_audit_leakage(parsed.file, target=parsed.target))
        sys.exit(exit_code)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
