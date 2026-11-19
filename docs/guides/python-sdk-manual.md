# Athena Python SDK Manual

## Overview
The `athena.sdk` package provides an asynchronous Python client (`AthenaClient`) for programmatically
interacting with Athena's REST and Server-Sent Events (SSE) analytics endpoints.
It enables data science teams to integrate Athena into Jupyter Notebooks, automated data pipelines,
and internal web applications.

## Installation & Import

The SDK is included with the core Athena distribution:

```python
from athena.sdk import AthenaClient
```

## Quick Start Example

```python
import asyncio
from athena.sdk import AthenaClient

async def main():
    async with AthenaClient(base_url="http://localhost:8000") as client:
        # 1. Health check
        health = await client.check_health()
        print("Server health:", health)

        # 2. Upload dataset
        upload_res = await client.upload_dataset("benchmark/datasets/telco_churn.csv")
        dataset_id = upload_res["dataset_id"]
        print(f"Uploaded dataset {dataset_id} with {upload_res['row_count']} rows")

        # 3. Create session
        session = await client.create_session(dataset_id=dataset_id)
        session_id = session["session_id"]

        # 4. Stream analytical execution
        print("\nStreaming analysis...")
        async for event in client.ask_stream(
            session_id=session_id,
            question="What is the churn rate across contract types?"
        ):
            print(f"[{event['event']}] {event['data']}")

asyncio.run(main())
```

## API Reference

### `AthenaClient(base_url, api_key=None, timeout=60.0)`
Initializes the HTTP client connection. Supports async context manager syntax (`async with`).

- `check_health() -> dict[str, str]`: Validates backend server readiness.
- `upload_dataset(file_path: str | Path) -> dict[str, Any]`: Streams file upload to `/api/datasets`.
- `get_profile(dataset_id: str) -> dict[str, Any]`: Fetches tabular statistical profile.
- `create_session(dataset_id: str) -> dict[str, Any]`: Starts stateful analytical session.
- `ask_stream(session_id: str, question: str) -> AsyncGenerator[dict[str, Any], None]`: Streams real-time tool execution, verifier passes, and final report.
- `get_run(run_id: str) -> dict[str, Any]`: Retrieves historical execution artifacts.
