# ADR-13: MCP Transport and Packaging

**Status:** Accepted
**Date:** 2026-10-08
**Decision:** D13 — MCP transport and packaging.

## Context
The brief requires exposing Athena's deterministic tools through an MCP server. The MCP SDK (Python, `mcp` package) supports multiple transports. The server must wrap existing tool functions, not reimplement them.

## Research Findings (verified 2026-10-08)
- **MCP Python SDK v2.3.0:** Uses `MCPServer` (not the older `Server`). Supports `stdio` and `sse` transports.
- **stdio transport:** Standard I/O — used by Claude Desktop and most MCP-capable clients. Simplest setup.
- **SSE transport:** HTTP-based — allows remote connections. More complex setup, needs a running HTTP server.
- **Streamable HTTP:** Newer transport option being standardized.

## Options

### Option A: stdio Transport Only (Recommended)
Package the MCP server as a CLI entry point that communicates over stdin/stdout.

| Dimension | Assessment |
|-----------|-----------|
| Complexity | Low — minimal transport code |
| Client compatibility | High — works with Claude Desktop, Cursor, and other MCP clients |
| Deployment | Simple — just a Python script |
| Remote access | No — requires local installation |
| Interview showcase | Good — demonstrates MCP integration |

### Option B: SSE Transport
Run the MCP server as an HTTP endpoint.

| Dimension | Assessment |
|-----------|-----------|
| Complexity | Medium — needs HTTP server setup |
| Client compatibility | Medium — not all clients support SSE transport |
| Deployment | Can be co-hosted with the main API |
| Remote access | Yes |
| Risk | Additional attack surface, CORS issues |

### Option C: Both stdio and SSE
Support both transports via a flag.

| Dimension | Assessment |
|-----------|-----------|
| Complexity | Medium-high |
| Risk | More code to maintain for marginal benefit |

## Decision
**Option A: stdio Transport Only.**

### Implementation

```python
# src/athena/mcp_server/server.py
from mcp import MCPServer
from athena.tools import profile_dataset, run_sql, stats_test, train_model, leakage_check, explain_model

server = MCPServer("athena-tools")

@server.tool("profile_dataset")
async def mcp_profile(dataset_path: str) -> dict:
    """Profile a dataset: row/column counts, dtypes, missingness, etc."""
    handle = DatasetHandle.from_path(dataset_path)
    result = await profile_dataset(handle)
    return result.model_dump()

# ... repeat for each tool

if __name__ == "__main__":
    server.run_stdio()
```

### Packaging
- Entry point in `pyproject.toml`: `athena-mcp = "athena.mcp_server.server:main"`
- After `pip install`, the user runs `athena-mcp` and configures their MCP client to use it.
- The MCP server creates its own DuckDB connection with the same hardening settings.

### Usage Documentation
Provide `docs/mcp-usage.md` with:
1. Installation instructions.
2. Claude Desktop configuration JSON:
   ```json
   {
     "mcpServers": {
       "athena": {
         "command": "athena-mcp",
         "args": []
       }
     }
   }
   ```
3. Python client example:
   ```python
   from mcp import ClientSession, StdioServerParameters
   params = StdioServerParameters(command="athena-mcp")
   async with ClientSession(*params) as session:
       result = await session.call_tool("profile_dataset", {"dataset_path": "data.csv"})
   ```

### Scope
The MCP server exposes these tools (read-only, same limits as main service):
- `profile_dataset`
- `run_sql`
- `recommend_test`
- `stats_test`
- `train_model`
- `leakage_check`
- `explain_model`

It does NOT expose: the orchestrator (no `ask_question`), the verifier, or any write operations.

## Consequences
- MCP server is a thin wrapper — changes to tools are automatically reflected.
- stdio is the simplest and most compatible transport.
- If SSE transport is needed later, it's a small addition.
- The MCP server is a late-stage deliverable (M7) — low risk to cut if time is short.
