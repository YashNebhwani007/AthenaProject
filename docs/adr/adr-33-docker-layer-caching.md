# ADR-33: Multi-Stage Docker Caching and Dependency Wheel Pre-Compilation

## Status
Accepted

## Context
Athena relies on heavy analytical packages including `scikit-learn`, `lightgbm`, `shap`, `duckdb`,
and `matplotlib`. Building the production Docker image without optimal layer caching results in
multi-minute rebuild times and bloated final image footprints exceeding 2GB.

## Decision
1. Implement a multi-stage Docker build separating the Python build environment from the minimal
   runtime container (`python:3.11-slim`).
2. Pre-compile binary wheels during the builder stage using `--no-cache-dir wheel`.
3. Copy only the installed site-packages and binary dynamic libraries into the final runtime container.
4. Separate `pyproject.toml` dependency resolution from source code copying to maximize Docker layer cache hits.

## Consequences
- Reduces final production container size from ~2.4GB to <680MB.
- CI/CD container build times drop from ~8 minutes to under 45 seconds when dependencies remain unchanged.
- Hardens container security by stripping compilers and build tools (`gcc`, `g++`, `make`) from runtime.
