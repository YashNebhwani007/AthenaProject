"""Dataset integrity and manifest hash verification script."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def calculate_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_datasets(base_dir: Path | None = None) -> int:
    """Verify all benchmark datasets exist, are non-empty, and print hashes."""
    root = base_dir or Path(__file__).resolve().parent.parent
    manifest_file = root / "benchmark" / "datasets" / "manifest.json"
    if not manifest_file.exists():
        sys.stderr.write(f"Manifest file not found: {manifest_file}\n")
        return 1

    with open(manifest_file, encoding="utf-8") as f:
        manifest = json.load(f)

    all_valid = True
    for ds in manifest.get("datasets", []):
        ds_id = ds["id"]
        rel_path = ds["path"]
        abs_path = root / rel_path

        if not abs_path.is_file():
            sys.stderr.write(f"ERROR: Dataset '{ds_id}' missing at {abs_path}\n")
            all_valid = False
            continue

        size = abs_path.stat().st_size
        if size == 0:
            sys.stderr.write(f"ERROR: Dataset '{ds_id}' is empty (0 bytes)\n")
            all_valid = False
            continue

        h = calculate_sha256(abs_path)[:12]
        print(f"Verified dataset [{ds_id}]: {size:,} bytes, sha256:{h}")

    return 0 if all_valid else 1


def main() -> None:
    code = verify_datasets()
    sys.exit(code)


if __name__ == "__main__":
    main()
