"""
backend/tests/test_security.py

Security boundary tests.

These tests verify that authorization is enforced at the API layer —
NOT in the frontend or middleware alone. Each test explicitly attempts
a forbidden operation and asserts a 401 or 403 response.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestUnauthenticatedAccess:
    """Every protected endpoint must return 401 when no token is provided."""

    PROTECTED_ENDPOINTS = [
        ("GET", "/api/v1/jobs"),
        ("GET", "/api/v1/resumes"),
        ("GET", "/api/v1/analytics/summary"),
        ("GET", "/api/v1/analytics/domain-dist"),
        ("GET", "/api/v1/admin/users"),
        ("GET", "/api/v1/admin/audit-logs"),
    ]

    @pytest.mark.parametrize("method,url", PROTECTED_ENDPOINTS)
    def test_no_token_returns_401(self, client: TestClient, method: str, url: str):
        resp = client.request(method, url)
        assert resp.status_code == 401, (
            f"{method} {url} returned {resp.status_code} instead of 401"
        )


class TestRoleEscalation:
    """Readonly/HR users must not be able to reach admin endpoints."""

    def test_hr_cannot_access_admin_users(self, client: TestClient, hr_token: str):
        resp = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        assert resp.status_code == 403

    def test_readonly_cannot_access_admin_users(self, client: TestClient, readonly_token: str):
        resp = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {readonly_token}"},
        )
        assert resp.status_code == 403

    def test_hr_cannot_access_audit_logs(self, client: TestClient, hr_token: str):
        resp = client.get(
            "/api/v1/admin/audit-logs",
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        assert resp.status_code == 403

    def test_readonly_cannot_create_job(self, client: TestClient, readonly_token: str):
        resp = client.post(
            "/api/v1/jobs",
            json={"title": "Injected Job", "requirements": []},
            headers={"Authorization": f"Bearer {readonly_token}"},
        )
        assert resp.status_code == 403

    def test_hr_cannot_deactivate_job(self, client: TestClient, hr_token: str, admin_token: str):
        # Create a job as HR first
        create_resp = client.post(
            "/api/v1/jobs",
            json={"title": "Target Job", "requirements": []},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert create_resp.status_code == 201
        job_id = create_resp.json()["public_id"]

        # HR should not be able to deactivate
        del_resp = client.delete(
            f"/api/v1/jobs/{job_id}",
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        assert del_resp.status_code == 403


class TestInvalidToken:
    """Tampered or expired tokens must be rejected."""

    def test_tampered_token_returns_401(self, client: TestClient, admin_token: str):
        # Tamper the token signature
        parts = admin_token.split(".")
        if len(parts) == 3:
            tampered = parts[0] + "." + parts[1] + ".invalidsignature"
        else:
            tampered = admin_token + "tampered"

        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tampered}"},
        )
        assert resp.status_code == 401

    def test_garbage_token_returns_401(self, client: TestClient):
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer thisisnotavalidjwt"},
        )
        assert resp.status_code == 401

    def test_missing_bearer_prefix_returns_401(self, client: TestClient, admin_token: str):
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": admin_token},  # missing "Bearer "
        )
        assert resp.status_code == 401
