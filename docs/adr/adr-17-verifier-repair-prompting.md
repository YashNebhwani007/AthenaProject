# ADR-17: Verifier Repair Prompt Engineering

**Status:** Accepted  
**Date:** 2026-11-15  
**Decision:** D17 — Trace-injected repair feedback loop for adversarial verification.

## Context
When Athena's 5-point verifier identifies violations (e.g., ungrounded literal numbers, causal language traps, missing citations), it enters a repair loop. Previously, the repair prompt only listed rule violation strings. LLMs often lacked awareness of which tool IDs and metric names were valid to cite, causing repeated validation errors.

## Decision
Inject structured trace context into the repair prompt:
- A list of valid tool result IDs (`t1`, `t2`, etc.), their tool names, and available metric keys.
- Concrete instructions on template placeholder syntax `{{tool_id.metric}}`.
- Strict schema reminder ensuring output remains valid Report JSON without conversational markdown.
