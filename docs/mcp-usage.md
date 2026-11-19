# Athena MCP Server Integration Guide

Athena exposes its entire suite of analytical tools over the open [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) using standard I/O (`stdio`) transport.

This allows AI assistants like Claude Desktop, Cursor, or custom LLM agent workflows to run SQL queries, compute hypothesis tests, evaluate target leakage, train models, and generate SHAP explanations on local datasets without re-implementing analytical tooling.

---

## 1. Quickstart & Installation

Ensure Athena is installed in your Python environment:

```bash
git clone https://github.com/YashNebhwani007/AthenaProject.git
cd AthenaProject
pip install -e .
```

Verify that the `athena-mcp` CLI entry point is functional:

```bash
athena-mcp --help
```

---

## 2. Claude Desktop Integration

To configure Athena with Claude Desktop, edit your `claude_desktop_config.json`:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

Add the Athena server definition:

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

If `athena-mcp` is installed inside a virtual environment, specify the full path to the executable:

```json
{
  "mcpServers": {
    "athena": {
      "command": "C:\\Users\\<username>\\AthenaProject\\.venv\\Scripts\\athena-mcp.exe",
      "args": []
    }
  }
}
```

Restart Claude Desktop. You will see a hammer icon 🔨 indicating that the following 8 Athena tools are loaded:
1. `profile_dataset`
2. `run_sql`
3. `stats_test`
4. `train_model`
5. `explain_model`
6. `predict_model`
7. `leakage_check`
8. `make_plot`

---

## 3. Python Client Example

You can connect to Athena directly from Python using the official `mcp` SDK:

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_athena_analysis():
    # Configure parameters to spawn the athena-mcp process
    server_params = StdioServerParameters(
        command="athena-mcp",
        args=[],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize connection handshake
            await session.initialize()

            # 1. List available tools
            tools = await session.list_tools()
            print("Connected tools:", [t.name for t in tools.tools])

            # 2. Profile a local dataset
            profile = await session.call_tool(
                "profile_dataset",
                arguments={"dataset_path": "demo_data/telco_churn.csv"},
            )
            print("Dataset Profile:", profile.content[0].text)

            # 3. Execute a validated SQL query
            sql_res = await session.call_tool(
                "run_sql",
                arguments={
                    "dataset_path": "demo_data/telco_churn.csv",
                    "query": "SELECT contract, count(*) as count, round(avg(monthly_charges), 2) as avg_charges FROM tbl_telco_churn GROUP BY contract",
                },
            )
            print("SQL Results:", sql_res.content[0].text)

            # 4. Check for target leakage
            leakage_res = await session.call_tool(
                "leakage_check",
                arguments={
                    "dataset_path": "demo_data/telco_churn.csv",
                    "target": "churn",
                },
            )
            print("Leakage Audit:", leakage_res.content[0].text)

if __name__ == "__main__":
    asyncio.run(run_athena_analysis())
```

---

## 4. Available Tools Reference

| Tool Name | Key Parameters | Output |
|-----------|----------------|--------|
| `profile_dataset` | `dataset_path` | Row/column count, null percentages, data quality warnings, suspected targets. |
| `run_sql` | `dataset_path`, `query` | Tabular query results, column names, execution metadata. |
| `stats_test` | `dataset_path`, `test_name`, `var1`, `var2`, `alpha` | Test statistic, p-value, effect size, statistical significance. |
| `train_model` | `dataset_path`, `target`, `split_strategy` | Held-out validation metrics, model artifact ID. |
| `explain_model` | `dataset_path`, `model_id`, `target`, `instance_idx` | SHAP global feature importances and local sample explanation. |
| `predict_model` | `dataset_path`, `features`, `model_id`, `target` | Prediction outcome, class probabilities, and confidence score. |
| `leakage_check` | `dataset_path`, `target` | High-confidence leakage warnings (ID detection, high correlation, duplicate rows). |
| `make_plot` | `dataset_path`, `plot_type`, `x`, `y`, `color`, `title` | Static PNG artifact and interactive Plotly JSON specification. |
