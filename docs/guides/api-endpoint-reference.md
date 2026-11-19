# Athena REST & SSE API Endpoint Reference

The Athena FastAPI server provides RESTful endpoints for dataset onboarding and session management,
alongside a Server-Sent Events (SSE) streaming endpoint for live execution trace and report delivery.

---

## 1. Endpoints Overview

| Method | Path | Description | Response Type |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Service health status and version string | `application/json` |
| `GET` | `/api/demo-datasets` | Pre-packaged benchmark demo datasets list | `application/json` |
| `POST` | `/api/datasets` | Upload a new CSV or Parquet dataset | `multipart/form-data` |
| `GET` | `/api/datasets/{id}/profile` | Retrieve exploratory summary and warnings | `application/json` |
| `POST` | `/api/sessions` | Create a new stateful analytical session | `application/json` |
| `POST` | `/api/sessions/{id}/ask` | Submit analytical prompt & stream execution | `text/event-stream` |
| `GET` | `/api/runs/{run_id}` | Retrieve historical run result and report | `application/json` |

---

## 2. Streaming Request Specification: `POST /api/sessions/{session_id}/ask`

### Request Body
```json
{
  "question": "What customer segments exhibit the highest churn probability?",
  "dataset_id": "telco_churn"
}
```

### Event Stream Format
The stream emits standard SSE events:
```
event: step_start
data: {"tool": "run_sql", "query": "SELECT contract, avg(churn) FROM tbl_telco_churn GROUP BY contract"}

event: step_complete
data: {"tool": "run_sql", "runtime_ms": 14.2, "metrics": [{"name": "month_to_month_churn", "value": 0.427}]}

event: report_delivered
data: {"question": "...", "tldr": "...", "findings": [...], "recommendations": [...]}
```
