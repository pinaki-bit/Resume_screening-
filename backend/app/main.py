"""
backend/app/main.py

FastAPI application factory — v0.2.0

Changes from v0.1.0:
  - All API routes now under /api/v1/ prefix
  - Legacy /auth/login and /health kept for backward compat (deprecated)
  - Added rate limiting via slowapi
  - All new routers registered
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import get_settings
from app.core.security import hash_password
from app.database import create_all_tables, get_db
from app.models.user import User

# Routers — new v1 namespace
from app.api.v1 import auth as auth_v1
from app.api.v1 import jobs as jobs_v1
from app.api.v1 import resumes as resumes_v1
from app.api.v1 import screening as screening_v1
from app.api.v1 import admin as admin_v1
from app.api.v1 import analytics as analytics_v1

# Legacy routers (kept for backward compat during migration)
from app.routers import health

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate limiter (shared instance — attached to app state)
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def _lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info("Starting %s v%s [%s]", settings.app_title, settings.app_version, settings.app_env)
    _init_db(settings)
    yield
    logger.info("Shutting down %s.", settings.app_title)


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title=settings.app_title,
        version=settings.app_version,
        description=(
            "AI-Powered Resume Screening & Candidate Intelligence System\n\n"
            "**Phase 1–3**: Authentication, health checks, job management, "
            "NLP/ML foundation.\n"
            "**Phase 4+**: Resume upload, screening, analytics, admin dashboard."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=_lifespan,
    )

    # ── Rate limiter state ──────────────────────────────────────────────────
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ── CORS ────────────────────────────────────────────────────────────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── v1 API routers ──────────────────────────────────────────────────────
    application.include_router(auth_v1.router)
    application.include_router(jobs_v1.router)
    application.include_router(resumes_v1.router)
    application.include_router(screening_v1.router)
    application.include_router(admin_v1.router)
    application.include_router(analytics_v1.router)

    # ── Legacy routers (deprecated — will be removed in v0.3.0) ────────────
    application.include_router(health.router)

    return application


# ---------------------------------------------------------------------------
# DB initialization helpers
# ---------------------------------------------------------------------------

def _init_db(settings) -> None:
    """Create all tables and seed the default admin if not present."""
    create_all_tables()
    _seed_admin(settings)


def _seed_admin(settings) -> None:
    db = next(get_db())
    try:
        existing = db.query(User).filter(
            User.email == settings.admin_email.lower()
        ).first()
        if not existing:
            admin = User(
                email=settings.admin_email.lower(),
                hashed_password=hash_password(settings.admin_password),
                full_name="System Administrator",
                role="admin",
                is_active=True,
                is_admin=True,
            )
            db.add(admin)
            db.commit()
            logger.info("Seeded admin user: %s", settings.admin_email)
        else:
            # Ensure legacy admin has the role field set correctly
            if existing.role != "admin":
                existing.role = "admin"
                existing.is_admin = True
                db.commit()
            logger.debug("Admin user already exists.")
    except Exception as exc:
        logger.error("Failed to seed admin user: %s", exc)
        db.rollback()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------

app = create_app()
