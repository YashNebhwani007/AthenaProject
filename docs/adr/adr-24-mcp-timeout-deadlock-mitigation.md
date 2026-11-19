# ADR-24: MCP Tool Timeout Handling and Deadlock Mitigation

## Status
Accepted

## Context
Athena integrates with Model Context Protocol (MCP) clients such as Claude Desktop over standard I/O (stdio).
If a deterministic tool encounters a long-running CPU operation (e.g. TreeSHAP computation on large feature matrices
or complex cross-tabulations) without yielding or timing out, the MCP transport hangs, leading to client-side disconnections.

## Decision
1. Wrap all MCP tool invocations with `asyncio.wait_for(timeout=settings.mcp_tool_timeout_seconds)`.
2. Default timeout configured to 30.0 seconds per tool execution.
3. On timeout expiration, return a structured `ToolResult(status=ToolStatus.error)` with informative diagnostic details rather than killing the server process.
4. Execute blocking CPU-bound computations (scikit-learn, shap, matplotlib) inside Python's `asyncio.to_thread` executor to preserve event loop liveness.

## Consequences
- The MCP stdio connection remains responsive even during heavy background computations.
- Claude Desktop receives clean JSON error descriptions instead of broken pipe exceptions.
- Prevents unbounded resource consumption on malformed user inputs.
