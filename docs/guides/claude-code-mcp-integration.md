# Configuring Claude Code with Athena MCP stdio Tools

## Overview
Athena provides a Model Context Protocol (MCP) server over standard input/output (`stdio`) and SSE.
This allows terminal-based AI developer tools like Anthropic's Claude Code CLI to natively discover and
execute Athena's deterministic analytical tools (DuckDB SQL queries, statistical tests, ML training,
and SHAP explanations).

## Configuration

To add Athena MCP tools to Claude Code, edit `~/.claude.json` or project-level `.mcp.json`:

```json
{
  "mcpServers": {
    "athena": {
      "command": "python",
      "args": ["-m", "athena.mcp_server.server"],
      "env": {
        "ATHENA_DATA_DIR": "./data"
      }
    }
  }
}
```

## Available Tools in Claude Code
Once configured, Claude Code displays the following native tool interfaces:
- `athena_profile_dataset`: Inspect tabular schema and summary statistics
- `athena_run_sql`: Execute safe read-only SQL queries via DuckDB
- `athena_run_stats`: Run t-tests, ANOVA, Chi-square, and Mann-Whitney U tests
- `athena_train_model`: Train gradient boosted classifiers/regressors
- `athena_explain_model`: Extract global and local SHAP feature importance
