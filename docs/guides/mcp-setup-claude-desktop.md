# Claude Desktop & Claude Code MCP Setup Manual

Athena provides a native Model Context Protocol (MCP) stdio server, allowing Anthropic's Claude Desktop
and Claude Code CLI to directly call Athena's deterministic analytical tools (DuckDB SQL, SciPy stats tests,
LightGBM training, and SHAP explainability).

---

## 1. Prerequisites
- Python 3.11+ installed with Athena dependencies (`pip install -e .`)
- Claude Desktop installed (macOS or Windows)

---

## 2. Configuration for Claude Desktop
Add Athena's MCP server configuration to your `claude_desktop_config.json`:

### Windows
Location: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "athena": {
      "command": "python",
      "args": ["-m", "athena.mcp_server.server"],
      "cwd": "C:\\Users\\yashb\\Downloads\\AthenaProject",
      "env": {
        "PYTHONPATH": "C:\\Users\\yashb\\Downloads\\AthenaProject\\src"
      }
    }
  }
}
```

---

## 3. Available MCP Tools
When connected, Claude Desktop has access to the following deterministic tools:
- `athena_profile`: Explore dataset dimensions, types, and null percentages.
- `athena_sql`: Execute read-only, AST-validated SQL against DuckDB.
- `athena_stats`: Recommend and execute hypothesis tests with effect sizes.
- `athena_ml`: Train baseline LightGBM classification or regression models.
- `athena_explain`: Compute global TreeSHAP values and feature contributions.
- `athena_predict`: Generate out-of-sample inference on novel input dictionaries.
