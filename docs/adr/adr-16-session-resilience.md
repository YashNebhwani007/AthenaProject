# ADR-16: Session Auto-Recovery and API Resilience

**Status:** Accepted  
**Date:** 2026-11-15  
**Decision:** D16 — Automatic state recovery for active sessions across server restarts.

## Context
When Athena server processes restart (or reload in development mode), in-memory session objects stored in the `sessions` dictionary are reset. Browser tabs holding older session IDs experienced `404 Not Found` when submitting questions, forcing manual page refreshes and losing context.

## Decision
1. **API Auto-Recovery:** If a question request (`POST /api/sessions/{session_id}/ask`) references an unrecognized session ID, the API inspects the payload for `dataset_id`. If valid, it transparently re-creates the session and re-registers the dataset.
2. **Frontend Disconnect Retry:** The React client (`App.tsx`) handles SSE network interruptions with a transparent single-attempt retry before surfacing UI errors.
