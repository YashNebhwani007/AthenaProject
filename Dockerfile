# Stage 1: Build React Frontend
FROM node:20-slim AS frontend
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend Environment
FROM python:3.11-slim AS backend
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security hardening
RUN groupadd -g 10001 athena && \
    useradd -u 10001 -g athena -s /bin/bash -m athena

COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

COPY src/ /app/src/
COPY demo_data/ /app/demo_data/
COPY benchmark/ /app/benchmark/
COPY --from=frontend /app/frontend/dist /app/static

RUN mkdir -p /app/data && chown -R athena:athena /app

USER athena

ENV DEMO_MODE=true
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "athena.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
