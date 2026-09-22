"""
frontend/services/api_client.py

Typed HTTP client for the Resume Screening API.

All calls go through this module so that:
  - The base URL is configured in one place.
  - Auth tokens are injected from session state automatically.
  - Error responses are parsed uniformly.
  - No raw requests.* calls appear in page code.
"""

from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
_TIMEOUT = 30  # seconds


class APIError(Exception):
    """Raised when the API returns a non-2xx response."""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API error {status_code}: {detail}")


def _headers() -> dict[str, str]:
    """Return auth headers from Streamlit session state."""
    token = st.session_state.get("access_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def _handle_response(resp: requests.Response) -> Any:
    """Raise APIError on non-2xx; otherwise return parsed JSON."""
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        raise APIError(resp.status_code, detail)
    if resp.content:
        return resp.json()
    return {}


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def login(email: str, password: str) -> dict:
    resp = requests.post(
        f"{API_BASE}/api/v1/auth/login",
        json={"email": email, "password": password},
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_me() -> dict:
    resp = requests.get(
        f"{API_BASE}/api/v1/auth/me",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

def list_jobs(active_only: bool = True) -> list[dict]:
    resp = requests.get(
        f"{API_BASE}/api/v1/jobs",
        params={"active_only": active_only},
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def create_job(payload: dict) -> dict:
    resp = requests.post(
        f"{API_BASE}/api/v1/jobs",
        json=payload,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_job(job_id: str) -> dict:
    resp = requests.get(
        f"{API_BASE}/api/v1/jobs/{job_id}",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def deactivate_job(job_id: str) -> dict:
    resp = requests.delete(
        f"{API_BASE}/api/v1/jobs/{job_id}",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


# ---------------------------------------------------------------------------
# Resumes
# ---------------------------------------------------------------------------

def upload_resume(file_bytes: bytes, filename: str, candidate_ref: str | None = None) -> dict:
    files = {"file": (filename, file_bytes, "application/pdf")}
    data = {}
    if candidate_ref:
        data["candidate_reference"] = candidate_ref
    resp = requests.post(
        f"{API_BASE}/api/v1/resumes/upload",
        files=files,
        data=data,
        headers=_headers(),
        timeout=60,
    )
    return _handle_response(resp)


def list_resumes(status_filter: str | None = None) -> list[dict]:
    params = {}
    if status_filter:
        params["status_filter"] = status_filter
    resp = requests.get(
        f"{API_BASE}/api/v1/resumes",
        params=params,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_resume(resume_id: str) -> dict:
    resp = requests.get(
        f"{API_BASE}/api/v1/resumes/{resume_id}",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


# ---------------------------------------------------------------------------
# Screening
# ---------------------------------------------------------------------------

def match_resume_to_job(job_id: str, resume_id: str) -> dict:
    resp = requests.post(
        f"{API_BASE}/api/v1/screening/{job_id}/match/{resume_id}",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_job_results(job_id: str, review_status: str | None = None) -> list[dict]:
    params = {}
    if review_status:
        params["review_status"] = review_status
    resp = requests.get(
        f"{API_BASE}/api/v1/screening/{job_id}/results",
        params=params,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def update_review(result_id: str, review_status: str, notes: str | None = None) -> dict:
    resp = requests.patch(
        f"{API_BASE}/api/v1/screening/results/{result_id}/review",
        json={"review_status": review_status, "review_notes": notes},
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

def get_summary() -> dict:
    resp = requests.get(
        f"{API_BASE}/api/v1/analytics/summary",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_domain_distribution() -> dict:
    resp = requests.get(
        f"{API_BASE}/api/v1/analytics/domain-dist",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_skill_heatmap(top_n: int = 15) -> dict:
    resp = requests.get(
        f"{API_BASE}/api/v1/analytics/skill-heatmap",
        params={"top_n": top_n},
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_score_distribution(job_id: str | None = None) -> dict:
    params = {}
    if job_id:
        params["job_id"] = job_id
    resp = requests.get(
        f"{API_BASE}/api/v1/analytics/score-hist",
        params=params,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

def list_users() -> list[dict]:
    resp = requests.get(
        f"{API_BASE}/api/v1/admin/users",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def create_user(payload: dict) -> dict:
    resp = requests.post(
        f"{API_BASE}/api/v1/admin/users",
        json=payload,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def update_user(user_id: int, payload: dict) -> dict:
    resp = requests.patch(
        f"{API_BASE}/api/v1/admin/users/{user_id}",
        json=payload,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_audit_logs(page: int = 1, event_type: str | None = None) -> dict:
    params = {"page": page}
    if event_type:
        params["event_type"] = event_type
    resp = requests.get(
        f"{API_BASE}/api/v1/admin/audit-logs",
        params=params,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def list_model_versions() -> list[dict]:
    resp = requests.get(
        f"{API_BASE}/api/v1/admin/model-versions",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)
