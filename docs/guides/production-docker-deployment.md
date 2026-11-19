# Production Docker Deployment & Hardening Manual

This manual details the steps to build, secure, and deploy Athena as a standalone containerized service.

---

## 1. Multi-Stage Build Architecture
Athena uses a two-stage Dockerfile:
1. **Frontend Builder:** Node 20 LTS Alpine image installs dependencies and builds Vite static bundle.
2. **Backend Runtime:** Python 3.11-slim Debian image installs Python wheels, copies static assets, and drops root privileges.

---

## 2. Hardening Constraints
- **Non-Root Execution:** Runs under user `athena` (`uid=10001, gid=10001`).
- **Read-Only Root Filesystem:** Container root mounted with `read_only: true`; write access limited to `/app/data/`.
- **Resource Constraints:** Memory limit `2G`, CPU quota `2.0`.
- **Ephemeral Temp Storage:** `/tmp` mounted via `tmpfs` with `noexec,nosuid,nodev` flags.

---

## 3. Running with Docker Compose
```bash
# Build and run Athena stack
docker compose up -d --build

# View container logs
docker compose logs -f athena-app

# Check health endpoint
curl http://localhost:8000/health
```

---

## 4. Environment Configuration
Pass API keys securely via environment file or secret store:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
PORT=8000
DATA_DIR=/app/data
ATHENA_DEMO_MODE=false
```
