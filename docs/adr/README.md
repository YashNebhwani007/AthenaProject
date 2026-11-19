# Architecture Decision Records (ADRs)

This directory documents all significant architectural and engineering decisions in Athena.

| ADR | Title | Status | Context & Core Decision |
|---|---|---|---|
| [ADR-01](adr-01-report-generation.md) | Report Generation & Verification Strategy | Accepted | Evidence-first claim-to-tool metric linking |
| [ADR-02](adr-02-orchestrator.md) | Orchestrator Architecture & Control Flow | Accepted | Autonomous ReAct-style loop with budget limits |
| [ADR-03](adr-03-llm-provider.md) | LLM Provider Strategy | Accepted | Unified multi-provider abstraction (OpenAI, Anthropic, Gemini, Groq) |
| [ADR-04](adr-04-sql-validation.md) | SQL Dialect & Validation Engine | Accepted | In-memory DuckDB with sqlglot AST read-only validation |
| [ADR-05](adr-05-ml-scope.md) | Machine Learning Tool Scope | Accepted | LightGBM classification and regression with automated leakage audit |
| [ADR-06](adr-06-stats-test-selection.md) | Statistical Test Selection & Correction | Accepted | Automated parametric/non-parametric tree with Bonferroni correction |
| [ADR-07](adr-07-verification.md) | Verifier Rule Formalization | Accepted | Formal implementation of rules V1 through V6 |
| [ADR-08](adr-08-frontend.md) | Frontend Architecture & Visualization | Accepted | Single-page modern UI with Plotly.js and streaming telemetry |
| [ADR-09](adr-09-deployment.md) | Deployment Target & Optimization | Accepted | Containerized deployment with memory bounds for cloud runtimes |
| [ADR-10](adr-10-benchmark.md) | Benchmark Suite Design & Ground Truth | Accepted | Multi-tier benchmark evaluation with deterministic ground truth |
| [ADR-11](adr-11-multi-table.md) | Multi-Table Architecture | Accepted | Cross-dataset relational queries via registered DuckDB views |
| [ADR-12](adr-12-persistence.md) | Session Persistence Strategy | Accepted | Stateful session cache with graceful cold-start recovery |
| [ADR-13](adr-13-mcp-transport.md) | MCP Transport & Packaging | Accepted | Model Context Protocol over stdio and SSE |
| [ADR-14](adr-14-predictive-inference.md) | Predictive Inference Tool Design | Accepted | Single-row and batch model inference with probability scoring |
| [ADR-15](adr-15-sql-metric-extraction.md) | Granular SQL Metric Extraction | Accepted | Automatic extraction of aggregate cells into numeric metrics |
| [ADR-16](adr-16-session-resilience.md) | Session Auto-Recovery & API Resilience | Accepted | Auto-reconnection and session reconstruction on server restarts |
| [ADR-17](adr-17-verifier-repair-prompting.md) | Verifier Repair Prompt Engineering | Accepted | Structured feedback prompts guiding LLM self-correction |
| [ADR-18](adr-18-benchmark-evaluation-strategy.md) | Multi-Model Benchmark Strategy | Accepted | Automated comparative evaluation across LLM providers |
| [ADR-19](adr-19-duckdb-table-aliasing.md) | DuckDB Table Aliasing & AST Safety | Accepted | Seamless dataset aliasing without schema pollution |
| [ADR-20](adr-20-sse-stream-normalization.md) | Frontend SSE Stream Normalization | Accepted | Standardized event schemas for client consumption |
| [ADR-21](adr-21-client-side-markdown-security.md) | Client-Side Markdown Security | Accepted | DOMPurify sanitization and KaTeX math rendering |
| [ADR-22](adr-22-web-worker-plot-offloading.md) | Web Worker Plot Offloading | Accepted | Non-blocking background rendering of heavy Plotly specs |
| [ADR-23](adr-23-dynamic-orchestration-routing.md) | Dynamic Fast-Path Routing | Accepted | Fast path execution for single-step deterministic queries |
| [ADR-24](adr-24-mcp-timeout-deadlock-mitigation.md) | MCP Timeout Deadlock Mitigation | Accepted | Bounded async tool timeouts with graceful failure cancellation |
| [ADR-25](adr-25-multi-table-join-ast-validation.md) | Multi-Table Join AST Validation | Accepted | AST verification of join keys and schema compatibility |
| [ADR-26](adr-26-duckdb-memory-disk-spill-policy.md) | DuckDB Memory Limit & Spill Policy | Accepted | 2GB memory ceiling with disk spillover to prevent OOM |
| [ADR-27](adr-27-fwer-and-fdr-multiplicity-control.md) | FWER & FDR Multiplicity Control | Accepted | Holm-Bonferroni and Benjamini-Hochberg multi-test corrections |
| [ADR-28](adr-28-vif-collinearity-pruning.md) | VIF Collinearity Pruning | Accepted | Variance Inflation Factor thresholding for multicollinearity |
| [ADR-29](adr-29-structured-logging-opentelemetry.md) | Structured Logging & OpenTelemetry | Accepted | JSONL trace emission with distributed context propagation |
| [ADR-30](adr-30-human-in-the-loop-checkpoints.md) | Human-in-the-Loop Checkpoints | Accepted | Interactive review checkpoints for high-risk recommendations |
| [ADR-31](adr-31-streaming-backpressure-buffer-sizing.md) | Streaming Backpressure & Buffering | Accepted | Bounded asyncio queue for SSE sessions |
| [ADR-32](adr-32-llm-sampling-determinism.md) | LLM Sampling Determinism | Accepted | Temperature 0.0 for analytical planning and verification |
| [ADR-33](adr-33-docker-layer-caching.md) | Multi-Stage Docker Caching | Accepted | Pre-compiled wheels and multi-stage container optimization |
| [ADR-34](adr-34-target-inference-heuristics.md) | Target Inference Heuristic Weighting | Accepted | Multi-factor heuristic for auto-detecting target columns |
| [ADR-35](adr-35-zero-variance-categorical-pruning.md) | Zero-Variance Predictor Pruning | Accepted | Automatic filtering of invariant predictors in LightGBM |
| [ADR-36](adr-36-causal-graph-acyclicity.md) | Causal Graph Acyclicity Validation | Accepted | DAG cycle detection prior to causal effect estimation |
| [ADR-37](adr-37-websocket-vs-sse-telemetry.md) | WebSocket vs SSE Evaluation | Accepted | Standardization on unidirectional Server-Sent Events |
| [ADR-38](adr-38-duckdb-rowgroup-pushdown.md) | DuckDB Parquet Row-Group Pushdown | Accepted | Parquet conversion and row-group pushdown optimization |
| [ADR-39](adr-39-persistent-audit-logging.md) | Persistent Audit Logging | Accepted | Append-only structured JSONL audit trails for AI governance |
| [ADR-40](adr-40-verifier-catastrophic-fallback.md) | Verifier Catastrophic Fallback | Accepted | Raw quantitative output fallback on exhausted repair retries |
