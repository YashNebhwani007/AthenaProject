"""Artifact cleanup script to purge temporary caches, plots, and database files."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def clean_artifacts(base_dir: Path | None = None) -> int:
    """Purge temporary cache files, generated plots, and test artifacts."""
    root = base_dir or Path(__file__).resolve().parent.parent
    targets = [
        root / "data" / "cache",
        root / "data" / "plots",
        root / "data" / "uploads",
        root / ".pytest_cache",
        root / ".ruff_cache",
    ]

    purged = 0
    for target in targets:
        if target.is_dir():
            shutil.rmtree(target, ignore_errors=True)
            print(f"Purged directory: {target.relative_to(root)}")
            purged += 1

    # Also clean *.pyc and __pycache__
    for p in root.rglob("__pycache__"):
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
            purged += 1

    print(f"Cleanup completed. Total targets purged: {purged}")
    return 0


def main() -> None:
    code = clean_artifacts()
    sys.exit(code)


if __name__ == "__main__":
    main()
