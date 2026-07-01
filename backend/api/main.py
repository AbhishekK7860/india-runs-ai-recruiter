"""FastAPI application entry point.

Assembles the India Runs AI Recruiter API by registering all routers and
applying global configuration sourced from AppSettings.
"""

from fastapi import FastAPI

from backend.api.routers import health, ranking
from backend.core.settings import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

# Health router has no prefix — exposes GET /health
app.include_router(health.router)

# Ranking router is mounted under /api/v1 — exposes POST /api/v1/rank
app.include_router(ranking.router, prefix="/api/v1")
