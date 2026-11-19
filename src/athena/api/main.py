"""FastAPI application entry point per Task 6.1."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from athena.api.routes import router

app = FastAPI(
    title="Athena AI — Autonomous Data Science Agent",
    description="Statistical rigor, automated verification, and evidence-grounded insights.",
    version="0.4.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API endpoints
app.include_router(router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint for deployment monitoring."""
    return {"status": "ok", "version": "0.4.0"}


# Serve built frontend static files if present
static_dir = Path("static")
if static_dir.exists():
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
