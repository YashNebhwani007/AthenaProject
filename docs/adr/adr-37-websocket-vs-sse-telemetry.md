# ADR-37: WebSocket vs SSE Protocol Evaluation for Real-Time Telemetry

## Status
Accepted

## Context
Athena streams multi-agent execution steps, tool results, verifier verdicts, and final reports
to the web UI and external clients. We evaluated whether to support bi-directional WebSockets
or unidirectional Server-Sent Events (SSE).

## Decision
1. Standardize on Server-Sent Events (`text/event-stream`) over HTTP/1.1 and HTTP/2 for all real-time telemetry.
2. WebSockets introduce unnecessary complexity around stateful connection pooling, proxy traversal,
   and load balancing across distributed containers.
3. SSE natively handles automatic reconnection, standard HTTP headers (including Bearer token auth),
   and works seamlessly behind standard reverse proxies (Nginx, Traefik, AWS ALB) without sticky sessions.

## Consequences
- Radically simplified client implementation (native browser `EventSource` and standard HTTP client libraries).
- Effortless horizontal scaling without complex WebSocket pub/sub message brokers.
- Consistent observability using standard HTTP access logs.
