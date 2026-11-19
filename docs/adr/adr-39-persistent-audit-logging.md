# ADR-39: Persistent Audit Logging for Compliance and Model Lineage

## Status
Accepted

## Context
Enterprise analytical environments demand traceable audit logs of all queries, data transformations,
statistical hypothesis tests, and verifier interventions. Debugging verification rejections and
tracking regulatory model compliance requires immutable record-keeping.

## Decision
1. Implement append-only structured JSONL logging for every orchestrator run in `data/audit/runs.jsonl`.
2. Each audit log entry captures: `run_id`, `timestamp_utc`, `dataset_id`, `user_query`,
   `tools_invoked`, `verifier_verdict`, `repairs_triggered`, and `model_card_hash`.
3. Provide an administrative query interface to inspect audit trails without exposing raw data payloads.

## Consequences
- Full regulatory compliance for data provenance and AI governance.
- Enables continuous monitoring of verifier pass/fail rates in production.
- Lightweight, zero-external-dependency audit implementation via append-only local files.
