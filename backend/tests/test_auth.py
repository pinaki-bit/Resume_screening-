"""
backend/tests/test_auth.py

Tests for POST /api/v1/auth/login, POST /api/v1/auth/logout, GET /api/v1/auth/me
"""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestLogin:
    def test_valid_credentials_returns_token(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "testpass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    def test_wrong_password_returns_401(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    def test_unknown_email_returns_401(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "testpass123"},
        )
        assert response.status_code == 401

    def test_missing_email_returns_422(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/login",
            json={"password": "testpass123"},
        )
        assert response.status_code == 422

    def test_short_password_returns_422(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "abc"},
        )
        assert response.status_code == 422

    def test_error_message_is_generic(self, client: TestClient):
        """Ensure error messages don't leak which field (email vs password) is wrong."""
        r1 = client.post("/api/v1/auth/login",
                         json={"email": "x@x.com", "password": "wrongwrong"})
        r2 = client.post("/api/v1/auth/login",
                         json={"email": "test@example.com", "password": "wrongwrong"})
        # Both should return 401 with the same generic message
        assert r1.status_code == 401
        assert r2.status_code == 401
        assert r1.json()["detail"] == r2.json()["detail"]


class TestMe:
    def test_me_returns_user(self, client: TestClient, admin_token: str):
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "test@example.com"
        assert data["role"] == "admin"
        assert "hashed_password" not in data

    def test_me_without_token_returns_401(self, client: TestClient):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_me_with_invalid_token_returns_401(self, client: TestClient):
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer notavalidtoken"},
        )
        assert resp.status_code == 401


class TestLogout:
    def test_logout_returns_200(self, client: TestClient, admin_token: str):
        resp = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200

    def test_logout_without_token_returns_401(self, client: TestClient):
        resp = client.post("/api/v1/auth/logout")
        assert resp.status_code == 401
