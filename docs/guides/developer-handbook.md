# Developer Handbook & Local Tooling Guide

## Overview
This document guides developers, contributors, and AI agents through the standard local development
workflows, code quality checks, and maintenance automation available in Athena.

## Prerequisites
- **Python:** 3.11+
- **Environment:** Linux, macOS, or Windows (WSL/PowerShell)
- **Package Manager:** `pip` or `uv`

## Common Commands (via Makefile or Shell)

| Target | Command | Purpose |
|---|---|---|
| `make install` | `pip install -e ".[dev]"` | Editable package install with test dependencies |
| `make lint` | `ruff check src/ tests/ scripts/` | Check code against Pyflakes and pycodestyle |
| `make format` | `ruff format src/ tests/ scripts/` | Format Python sources to 100 char limit |
| `make test` | `pytest tests/ -v` | Run full unit and integration test suite |
| `make benchmark`| `python -m scripts.run_benchmarks` | Run benchmark smoke evaluation suite |
| `make clean` | `python -m scripts.clean_artifacts` | Purge temporary cache files and test plots |
| `make run` | `uvicorn athena.api.main:app` | Start local development server on port 8000 |

## Verification Automation Scripts

Athena includes dedicated maintenance scripts in `scripts/`:

1. **`python -m scripts.verify_datasets`:**
   Inspects all datasets in `benchmark/datasets/manifest.json`, validates file presence, non-zero size,
   and prints SHA-256 integrity checksums.

2. **`python -m scripts.validate_docs`:**
   Parses all relative Markdown links in `README.md` and `docs/`, confirming that all target documents
   and images exist on disk.

3. **`python -m scripts.clean_artifacts`:**
   Removes generated plots, compiled bytecode (`__pycache__`), and temporary test databases.
