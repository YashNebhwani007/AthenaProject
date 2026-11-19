# ADR-29: Structured Log Ingestion and OpenTelemetry Trace Context

## Status
Accepted

## Context
Athena runs multiple asynchronous concurrent steps: LLM streaming, DuckDB query execution,
hypothesis testing, and verifier repair iterations. Debugging distributed failures or latency
spikes across sessions requires unified correlation IDs and trace propagation.

## Decision
1. Standardize all application logging on structured JSON formatted by `structlog`.
2. Inject W3C Trace Context headers (`traceparent`, `tracestate`) into all outbound LLM API requests and incoming SSE connections.
3. Every log event must include four mandatory fields:
   - `session_id`: Unique identifier for the user's analytical session.
   - `run_id`: Unique execution run identifier.
   - `dataset_id`: Dataset currently being operated on.
   - `duration_ms`: Duration of the specific operation in milliseconds.
4. Support standard OpenTelemetry collector export via HTTP/gRPC when configured.

## Consequences
- End-to-end observability from client click through SSE stream to DuckDB query execution.
- High-fidelity log search in Datadog, Grafana Loki, or Google Cloud Logging.
- Standardized error event schemas simplify automated health monitoring and alerting.
