# ADR-31: Streaming Token Backpressure and Client Buffer Sizing

## Status
Accepted

## Context
During live SSE streaming of analytical trace events and multi-step tool outputs,
the FastAPI backend can generate events faster than slow client connections can process them.
Without backpressure controls, unbounded queue growth risks memory exhaustion on the server.

## Decision
1. Implement a bounded `asyncio.Queue(maxsize=100)` for all SSE session streams.
2. If the client buffer fills up, the orchestrator awaits queue capacity before executing next tool steps.
3. Automatically configure client-side event buffer timeout to 45 seconds before flagging connection timeout.
4. If a client disconnects unexpectedly, gracefully terminate background task execution and clean up DuckDB handles.

## Consequences
- Guaranteed memory safety on the FastAPI server during slow client reads.
- Prevents orphaned long-running analytical tool tasks from consuming server resources.
- Clean client reconnection and stream resumption semantics.
