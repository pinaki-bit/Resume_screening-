"""
backend/app/routers/health.py

Health-check endpoints.

GET /health        — liveness probe (always returns 200 if the process is up)
GET /health/db     — readiness probe (checks DB connectivity)
"""

from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings
from app.database import check_db_connection

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    summary="Liveness probe",
    response_description="Basic application status",
)
def health_check() -> dict:
    """
    Returns a simple liveness signal.

    Use this endpoint as a Kubernetes liveness probe or a load-balancer
    health check.  It does **not** touch the database.
    """
    settings = get_settings()
    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.app_env,
    }


@router.get(
    "/db",
    summary="Database readiness probe",
    response_description="Database connectivity status",
)
def health_db() -> dict:
    """
    Returns the database connectivity status.

    Runs a lightweight `SELECT 1` against the configured database.
    Returns HTTP 200 with `{"status": "ok"}` when reachable, or
    HTTP 200 with `{"status": "error"}` when unreachable (intentional —
    infrastructure probes should read the body, not just the status code).
    """
    connected = check_db_connection()
    return {
        "status": "ok" if connected else "error",
        "database": "connected" if connected else "unreachable",
    }
