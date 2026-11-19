# ADR-20: Frontend SSE Stream Normalization

**Status:** Accepted  
**Date:** 2026-11-15  
**Decision:** D20 — Cross-platform Server-Sent Events (SSE) buffer chunk parsing.

## Context
FastAPI's SSE streaming sends chunked events separated by newlines (`\n\n`). On Windows hosts or specific reverse proxies, chunks may arrive with CRLF (`\r\n\r\n`) or split across packet boundaries. Standard regex splitting on `\n\n` caused dropped events and frozen frontend states.

## Decision
In `frontend/src/api/client.ts`:
1. Normalize incoming chunk buffers by replacing `\r\n` with `\n`.
2. Maintain an unconsumed buffer across stream reads until complete event blocks (`\n\n`) are received.
3. Emit typed event objects matching Athena's `EventType` lifecycle.
