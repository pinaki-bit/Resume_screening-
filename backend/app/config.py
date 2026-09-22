"""
backend/app/config.py

Application settings loaded from environment variables / .env file.
Uses Pydantic v2 BaseSettings so every value is type-validated at startup.

Adding a new setting:
  1. Add the field here with a sensible default.
  2. Add it to .env.example with a comment.
  3. Never hardcode secrets — use environment variables or a secret manager.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root — three levels up from this file: app/ → backend/ → root
_BACKEND_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        protected_namespaces=(),   # allow field names starting with "model_"
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    app_env: str = "development"
    app_title: str = "Resume Intelligence API"
    app_version: str = "0.2.0"

    # ------------------------------------------------------------------
    # Security / JWT
    # ------------------------------------------------------------------
    secret_key: str = "CHANGE_ME_USE_openssl_rand_hex_32"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    database_url: str = "sqlite:///./resume_screening.db"

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    allowed_origins: str = "http://localhost:8501,http://127.0.0.1:8501"

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _keep_origins_string(cls, v: str) -> str:
        return v

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    # ------------------------------------------------------------------
    # File upload
    # ------------------------------------------------------------------
    upload_dir: str = str(_BACKEND_ROOT / "uploads")
    max_upload_size_mb: int = 10          # megabytes
    allowed_extensions: str = "pdf"       # comma-separated

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def allowed_extension_set(self) -> set[str]:
        return {ext.strip().lower() for ext in self.allowed_extensions.split(",")}

    # ------------------------------------------------------------------
    # ML / model artifacts
    # ------------------------------------------------------------------
    model_dir: str = str(_BACKEND_ROOT.parent / "ml" / "artifacts")
    active_model_filename: str = "model_latest.joblib"

    @property
    def active_model_path(self) -> str:
        return os.path.join(self.model_dir, self.active_model_filename)

    # ------------------------------------------------------------------
    # NLP
    # ------------------------------------------------------------------
    spacy_model: str = "en_core_web_sm"

    # Path to shared skill taxonomy (relative to backend root)
    skill_taxonomy_path: str = str(
        _BACKEND_ROOT.parent / "shared" / "skill_taxonomy.json"
    )
    label_mapping_path: str = str(
        _BACKEND_ROOT.parent / "shared" / "label_mapping.json"
    )

    # ------------------------------------------------------------------
    # Email / SMTP
    # ------------------------------------------------------------------
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    email_from: str = "noreply@example.com"
    email_enabled: bool = False           # Set True in production

    # ------------------------------------------------------------------
    # Rate limiting (requests per window)
    # ------------------------------------------------------------------
    rate_limit_login: str = "10/minute"
    rate_limit_upload: str = "20/minute"
    rate_limit_default: str = "200/minute"

    # ------------------------------------------------------------------
    # Seed admin (dev only — override in production)
    # ------------------------------------------------------------------
    admin_email: str = "admin@example.com"
    admin_password: str = "changeme123"

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    log_level: str = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance (loaded once per process)."""
    return Settings()
