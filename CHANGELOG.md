# Athena Project Changelog

All notable changes to the Athena Autonomous Data Science Agent are documented in this file.

---

## [0.4.0] - 2026-11-19

### Added
- **Python Client SDK (`athena.sdk`):**
  - High-performance asynchronous `AthenaClient` supporting connection pooling and async context manager.
  - Native file streaming for CSV/Parquet dataset registration via `upload_dataset()`.
  - Generator-based Server-Sent Events (SSE) consumer via `ask_stream()` with structured event normalization.
  - Full SDK getting-started guide and Jupyter Notebook integration examples.
- **Benchmark Evaluation Suite Expansion:**
  - Expanded benchmark evaluation suite to 47 questions across SQL, stats, ML, leakage, causal, and refusal categories.
  - Added new questions and ground truth computations: `churn_sql_04`, `titanic_sql_03`, `income_sql_03`, `refusal_04`, and `causal_03`.
  - Deterministic ground truth compilation and verification in `benchmark/ground_truth/expected.json`.
- **Architectural Decision Records (ADRs 31 to 40):**
  - ADR-31: Streaming Token Backpressure and Client Buffer Sizing.
  - ADR-32: LLM Temperature and Top-p Sampling Policies for Analytical Determinism.
  - ADR-33: Multi-Stage Docker Caching and Dependency Wheel Pre-Compilation.
  - ADR-34: Automated Target Inference Heuristic Weighting.
  - ADR-35: Handling Zero-Variance Categorical Predictors in LightGBM.
  - ADR-36: Automated Causal Graph Acyclicity Validation.
  - ADR-37: WebSocket vs SSE Protocol Evaluation for Real-Time Telemetry.
  - ADR-38: DuckDB Parquet Row-Group Pushdown Optimization.
  - ADR-39: Persistent Audit Logging for Compliance and Model Lineage.
  - ADR-40: Fallback Strategy for Catastrophic Verifier Rejection Loops.
- **Advanced Technical Guides:**
  - Statistical effect size interpretation and Cohen benchmarks (`docs/guides/statistical-effect-sizes.md`).
  - Handling class imbalance in tabular predictive pipelines (`docs/guides/class-imbalance-strategies.md`).
  - AST sqlglot custom transpilation for DuckDB dialect (`docs/guides/ast-sqlglot-transpilation.md`).
  - TreeSHAP vs KernelSHAP performance trade-offs (`docs/guides/treeshap-performance-tuning.md`).
  - Claude Code integration with Athena MCP stdio tools (`docs/guides/claude-code-mcp-integration.md`).
  - Time-series leakage detection and temporal validation splits (`docs/guides/time-series-leakage-detection.md`).
  - Structuring executive reports with evidence citations (`docs/guides/executive-report-structuring.md`).
  - DuckDB secure connection creation and pragma sandboxing (`docs/guides/duckdb-secure-connection-pragma.md`).
  - Local GPU acceleration for LightGBM and CUDA fallbacks (`docs/guides/gpu-acceleration-lightgbm.md`).
  - Local development tooling and Makefile guide (`docs/guides/developer-handbook.md`).
- **Developer Tooling, Scripts & Automation:**
  - Root `Makefile` with targets (`install`, `lint`, `format`, `test`, `benchmark`, `clean`, `run`).
  - Dataset integrity verification script (`scripts/verify_datasets.py`) with SHA-256 checks.
  - Documentation link validator (`scripts/validate_docs.py`).
  - Artifact cache purge script (`scripts/clean_artifacts.py`).
  - Automated benchmark evaluation runner (`scripts/run_benchmarks.py`).
- **Quality & Testing:**
  - Full test suite passing across all 196 unit and integration test assertions.
  - Full Ruff formatting and strict Pyflakes compliance across all modules.

---

## [0.3.0] - 2026-11-19

### Added
- **Command-Line Interface (`athena`):** First-class CLI utility with subcommands:
  - `athena profile <file> [--json]`: Generates comprehensive dataset column statistics and quality alerts.
  - `athena query <file> --sql <query>`: Executes AST-validated, read-only SQL queries via DuckDB.
  - `athena audit-leakage <file> --target <col>`: Runs 6 independent target leakage checks.
- **Architectural Decision Records (ADRs 21 to 30):**
  - ADR-21: Client-Side Markdown Rendering & KaTeX Sanitization.
  - ADR-22: Web Worker Offloading for Large Interactive Visualizations.
  - ADR-23: Dynamic Fast-Path vs Deep-Verification Routing.
  - ADR-24: MCP Tool Timeout Handling and Deadlock Mitigation.
  - ADR-25: Multi-Table Join AST Validation & Schema Reflection.
  - ADR-26: DuckDB Memory Limit and Disk Spill Policy.
  - ADR-27: Automated Family-Wise Error Rate and FDR Control.
  - ADR-28: Variance Inflation Factor (VIF) Collinearity Pruning.
  - ADR-29: Structured Log Ingestion and OpenTelemetry Trace Context.
  - ADR-30: Human-in-the-Loop Interactive Verification Checkpoints.
- **Operational Guides:**
  - Claude Desktop & Claude Code MCP integration manual.
  - Frontend architecture & SSE streaming state manual.
  - DuckDB AST security sandbox and sqlglot validator specification.
  - Hypothesis testing multiplicity correction guide.
  - LightGBM architecture & cross-validation manual.
  - Synthetic benchmark ground truth generation guide.
  - Production Docker deployment and container hardening manual.
  - Contributor workflow & release checklist.
  - REST & SSE API endpoint integration reference.
  - Athena CLI usage reference manual.
- **Production Container Hardening:**
  - Hardened Dockerfile with non-root user (`uid=10001`).
  - Production `docker-compose.yml` local orchestration stack.
  - `.dockerignore` for minimal image footprint.
- **Test Suite Expansion:** Over 170 unit tests across tools, verifier, schemas, API, MCP, and CLI.

---

## [0.2.0] - 2026-11-19

### Added
- Model Context Protocol (MCP) server integration (`athena-mcp`).
- Predictive inference deterministic tool (`predict_model`).
- Granular SQL metric extraction and automatic table aliasing.
- ADRs 14 to 20 covering resilient session recovery, SSE stream normalization, and benchmark strategies.
- Comprehensive dataset dictionaries for Telco Churn, California Housing, Adult Income, and Titanic.

---

## [0.1.0] - 2026-10-10

### Added
- Core Athena autonomous orchestrator and tool execution engine.
- 5-point adversarial verifier (V1-V5) with automated repair prompting loop.
- FastAPI backend with Server-Sent Events (SSE) streaming.
- React 18 frontend with interactive Plotly visualizations.
- Initial benchmark suite and evaluation runner.
