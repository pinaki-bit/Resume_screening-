"""
backend/app/main.py

FastAPI application factory — v0.3.0

Security enhancements:
  - CORS restricted to specific methods/headers (no wildcards)
  - API docs conditionally disabled in production
  - Startup security checks (refuses insecure production configs)
  - Rate limiter registered for login/upload enforcement
  - Default admin seeded with must_change_password=True
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings, startup_security_checks
from app.core.security import hash_password
from app.database import create_all_tables, get_db
from app.models.user import User
from app.rate_limiter import limiter

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
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def _lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()

    # --- Security checks before anything else ---
    startup_security_checks(settings)

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
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        openapi_url=settings.openapi_url,
        lifespan=_lifespan,
    )

    # ── Rate limiter state ──────────────────────────────────────────────────
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ── CORS — restricted methods and headers (no wildcards) ────────────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
    )

    # ── Security headers middleware ─────────────────────────────────────────
    @application.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )
        return response

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
                # Force password change if using default credentials
                must_change_password=settings.has_default_admin_password,
            )
            db.add(admin)
            db.commit()
            if settings.has_default_admin_password:
                logger.warning(
                    "⚠️  Seeded admin user '%s' with DEFAULT password. "
                    "The admin will be forced to change it on first login.",
                    settings.admin_email,
                )
            else:
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
