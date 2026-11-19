# Contributor Workflow & Release Checklist

This guide documents the procedures for contributing to Athena, maintaining code quality,
and releasing new semantic versions.

---

## 1. Development Environment Setup
```bash
# Clone repository
git clone https://github.com/YashNebhwani007/AthenaProject.git
cd AthenaProject

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install editable package with dev dependencies
pip install -e ".[dev]"
```

---

## 2. Pre-Commit Quality Checks
All pull requests must pass local Ruff linting and formatting without warnings:
```bash
ruff check src/ tests/ benchmark/
ruff format --check src/ tests/ benchmark/
pytest tests/ -v
```

---

## 3. Conventional Commits Standard
Commit messages must adhere to Conventional Commits:
- `feat:` New features, analytical tools, or UI components.
- `fix:` Bug fixes, verifier rule adjustments, or error handling.
- `docs:` Documentation, ADRs, or dataset dictionaries.
- `test:` Unit tests, edge-case tests, or benchmark ground truth.
- `refactor:` Code improvements that preserve public interfaces.
- `chore:` Dependency bumps, CI configuration, or build scripts.

---

## 4. Release Checklist
1. Update `pyproject.toml` version following Semantic Versioning (`MAJOR.MINOR.PATCH`).
2. Update version badge in `README.md`.
3. Verify all 160+ unit tests pass cleanly: `pytest tests/`.
4. Run full smoke benchmark evaluation: `python -m benchmark.runner --questions smoke`.
5. Tag release commit: `git tag -a v0.X.X -m "Release v0.X.X"`.
