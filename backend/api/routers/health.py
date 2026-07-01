"""Health check router.

Provides a GET /health endpoint for liveness probing. Returns the
application version and a static status string.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.core.settings import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(tags=["health"])

HEALTH_ROUTE = "/health"


class HealthResponse(BaseModel):
    """Response model for the health check endpoint."""

    status: str
    version: str


@router.get(HEALTH_ROUTE, response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return service liveness status and current application version.

    Returns:
        HealthResponse with status='ok' and the configured app version.
    """
    try:
        logger.info("Health check requested", route=HEALTH_ROUTE)
        return HealthResponse(status="ok", version=settings.APP_VERSION)
    except Exception:
        logger.exception("Unexpected error in health_check", route=HEALTH_ROUTE)
        raise
