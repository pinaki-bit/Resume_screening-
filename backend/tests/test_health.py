"""
backend/tests/test_health.py

Tests for GET /health and GET /health/db endpoints.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestHealthLiveness:
    def test_returns_200(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200

    def test_status_is_ok(self, client: TestClient):
        data = response = client.get("/health").json()
        assert data["status"] == "ok"

    def test_version_present(self, client: TestClient):
        data = client.get("/health").json()
        assert "version" in data
        assert data["version"]  # non-empty string

    def test_environment_present(self, client: TestClient):
        data = client.get("/health").json()
        assert "environment" in data


class TestHealthDB:
    def test_returns_200(self, client: TestClient):
        response = client.get("/health/db")
        assert response.status_code == 200

    def test_database_connected(self, client: TestClient):
        data = client.get("/health/db").json()
        # In test environment the in-memory SQLite DB should be reachable
        assert data["status"] == "ok"
        assert data["database"] == "connected"
