# Athena Project Changelog

All notable changes to the Athena Autonomous Data Science Agent are documented in this file.

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
