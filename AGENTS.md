# Athena Developer & AI Agent Guidelines

This document outlines architectural constraints, code style standards, testing requirements, and procedures for extending Athena.

---

## 1. Code Style & Tooling

Athena adheres to strict Python quality standards:

- **Python Version:** 3.11+
- **Linter & Formatter:** [Ruff](https://docs.astral.sh/ruff/)
  - Target version: `py311`
  - Max line length: 100 characters
  - Rules: `E` (pycodestyle errors), `F` (Pyflakes), `I` (isort imports)
- **Typing:** Strict type annotations on all function signatures and public APIs.
- **Schemas:** All data models must use Pydantic v2 (`BaseModel`, `Field`, `model_dump()`).

Run linter checks before committing:
```bash
ruff check src/ tests/ benchmark/
ruff format --check src/ tests/ benchmark/
```

---

## 2. Testing Conventions

- **Framework:** `pytest` with `pytest-asyncio` and `pytest-cov`.
- **Test File Naming:** `tests/test_*.py` or `tests/<subsystem>/test_*.py`.
- **Async Tests:** Decorate async test coroutines with `@pytest.mark.asyncio`.
- **Deterministic Tool Testing:** Always test deterministic tools against real DuckDB instances and real pandas DataFrames rather than shallow mocks. Only LLM client API calls should be mocked or replayed from cache during CI.
- **Verification Rule Testing:** Every verifier rule in `src/athena/verify/rules.py` must maintain at least 3 positive (passing) test cases and 3 negative (failing) edge-case tests in `tests/test_verifier_rules.py`.

Run tests:
```bash
pytest tests/ -v
```

---

## 3. How to Add a New Deterministic Tool

To add a new deterministic analytical tool to Athena:

1. **Implement Tool Function:**
   Create or edit a module in `src/athena/tools/`:
   ```python
   from typing import Any
   from athena.data.registry import DatasetRegistry
   from athena.data import default_registry
   from athena.schemas import Metric, ToolResult, ToolStatus
   from athena.tools.base import register_tool, tool_fn

   @register_tool("my_tool")
   @tool_fn("my_tool")
   async def my_tool(
       dataset_id: str,
       param: str,
       registry: DatasetRegistry | None = None,
   ) -> ToolResult:
       reg = registry or default_registry
       conn = reg.get_connection(dataset_id)
       handle = reg.get(dataset_id)

       # Compute deterministic result
       metric_val = 42.0

       return ToolResult(
           id="",  # Auto-populated by @tool_fn decorator
           tool="my_tool",
           args={"dataset_id": dataset_id, "param": param},
           status=ToolStatus.ok,
           output={"result": metric_val},
           metrics=[Metric(name="my_metric", value=metric_val, unit="count")],
           artifacts=[],
           warnings=[],
           runtime_ms=0,  # Auto-measured by @tool_fn
       )
   ```

2. **Export in Tools Package:**
   Add the tool export to `src/athena/tools/__init__.py`.

3. **Expose via MCP Server:**
   Add a decorated `@server.tool()` wrapper in `src/athena/mcp_server/server.py`.

4. **Write Tests:**
   Add comprehensive test coverage in `tests/tools/test_my_tool.py`.

---

## 4. How to Add a Benchmark Question

To add an evaluation case to the Athena Benchmark suite:

1. **Add Entry to `benchmark/questions/questions.json`:**
   ```json
   {
     "id": "q43",
     "dataset": "telco_churn",
     "category": "descriptive",
     "question": "What is the average tenure of customers?",
     "expected_claims": {
       "type": "numeric",
       "metric": "avg_tenure",
       "tolerance": 0.01
     }
   }
   ```

2. **Implement Ground Truth Computation:**
   Add the exact ground truth script in `benchmark/ground_truth/` computing the reference value via pandas/duckdb.

3. **Regenerate `expected.json`:**
   Update `benchmark/ground_truth/expected.json` with the ground-truth output.

4. **Run Smoke Suite:**
   ```bash
   python -m benchmark.runner --systems A1 --questions smoke
   ```

---

## 5. Git Commit Format

We use standard Conventional Commits:

- `feat:` New features, tools, or UI components (e.g. `feat(mcp): add stdio server`)
- `fix:` Bug fixes or repair loop improvements (e.g. `fix(verifier): handle empty recommendations`)
- `test:` Unit, integration, or benchmark tests (e.g. `test(tools): add SHAP explain tests`)
- `docs:` Documentation and ADR additions (e.g. `docs(mcp): add claude desktop config guide`)
- `refactor:` Code improvements without altering external behavior (e.g. `refactor(api): stream events cleanly`)
