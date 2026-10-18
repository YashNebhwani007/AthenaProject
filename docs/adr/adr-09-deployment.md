# ADR-09: Deployment Target and Cost

**Status:** Accepted
**Date:** 2026-10-08
**Decision:** D9 — Deployment target and cost (free-tier options), including how demo datasets and secrets are handled.

## Context
The project needs a public live demo. Budget is free-tier or very low cost. The application is a Python backend (FastAPI) + React frontend (static files) + DuckDB (in-memory).

## Research Findings (verified 2026-10-08)
- **Render free tier:** 750 free instance hours/month, 512 MB RAM, 0.1 CPU. 15-minute spin-down on inactivity. Free PostgreSQL (90 days). Custom domains. Docker support.
- **Hugging Face Spaces:** Free "CPU Basic" tier may not be available for new Docker spaces.
- **Railway:** Free tier: 500 hours/month, 512 MB RAM. Similar to Render.
- **Fly.io:** Free tier: 3 shared VMs, 256 MB RAM each. More complex setup.

## Options

### Option A: Render Free Tier (Recommended)
Deploy as a single Docker container on Render's free tier.

| Dimension | Assessment |
|-----------|-----------|
| Cost | Free (within 750 hours/month) |
| RAM | 512 MB — tight but workable with dataset size limits |
| Spin-down | 15 minutes inactivity → cold start (~30s for Python app) |
| Setup complexity | Low — Dockerfile + render.yaml |
| Custom domain | Yes (free) |
| Docker support | Yes |

### Option B: Railway Free Tier
Similar to Render but slightly different limits.

| Dimension | Assessment |
|-----------|-----------|
| Cost | Free (within 500 hours/month) |
| RAM | 512 MB |
| Setup complexity | Low |
| Risk | Railway has changed free tier terms multiple times |

### Option C: Fly.io Free Tier
More control but more complexity.

| Dimension | Assessment |
|-----------|-----------|
| Cost | Free for small VMs |
| RAM | 256 MB — too tight for DuckDB + ML |
| Setup complexity | Medium-high — requires flyctl, Fly-specific config |
| Risk | 256 MB is likely insufficient |

## Decision
**Option A: Render Free Tier.**

### Deployment Architecture
```
Single Docker Container on Render
├── FastAPI backend (serves API + static frontend)
├── DuckDB (in-memory, per-session)
├── Pre-loaded demo datasets (bundled in image)
└── Static React build (served by FastAPI)
```

### Demo Configuration
- **Demo datasets:** 3 preloaded public datasets (Telco Churn, Adult Income, California Housing) bundled into the Docker image under `/app/demo_data/`.
- **User uploads:** Disabled on demo deployment (or capped at 5 MB, 50K rows) via `DEMO_MODE=true` env var.
- **Secrets:** `LLM_API_KEY` set as Render environment variable. `.env.example` committed with placeholder values.
- **Cold start:** Add a health check endpoint. Consider a UptimeRobot ping to reduce cold starts (free tier, every 5 min).

### Dockerfile Strategy
```dockerfile
# Multi-stage build
FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/ .
RUN npm ci && npm run build

FROM python:3.11-slim AS backend
WORKDIR /app
COPY --from=frontend /app/frontend/dist /app/static
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY src/ /app/src/
COPY demo_data/ /app/demo_data/
EXPOSE 8000
CMD ["uvicorn", "athena.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Resource Limits for Demo
| Resource | Demo Limit | Full Limit |
|----------|-----------|------------|
| File size | 5 MB | 50 MB |
| Rows | 50,000 | 500,000 |
| Columns | 200 | 500 |
| DuckDB memory | 256 MB | 512 MB |
| SHAP subsample | 500 rows | 1,000 rows |
| Orchestrator steps | 15 | 30 |

## Consequences
- Cold start latency is a UX issue — add a loading indicator and consider keep-alive pinging.
- 512 MB RAM constraint means strict dataset size enforcement.
- Single-container deployment is simple to maintain.
- If Render changes free tier terms, migration to Railway is straightforward (same Docker image).
