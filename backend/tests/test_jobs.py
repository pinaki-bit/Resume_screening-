"""
backend/tests/test_jobs.py

Tests for the Job CRUD API and role-based access control.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


SAMPLE_JOB = {
    "title": "Data Scientist",
    "department": "Analytics",
    "description": "Looking for a data scientist with ML experience.",
    "domain": "Data Science",
    "requirements": [
        {"skill_name": "Python", "is_required": True, "weight": 1.5},
        {"skill_name": "scikit-learn", "is_required": True, "weight": 1.0},
        {"skill_name": "TensorFlow", "is_required": False, "weight": 0.5},
    ],
}


class TestCreateJob:
    def test_hr_can_create_job(self, client: TestClient, hr_token: str):
        resp = client.post(
            "/api/v1/jobs",
            json=SAMPLE_JOB,
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Data Scientist"
        assert "public_id" in data
        assert len(data["requirements"]) == 3

    def test_admin_can_create_job(self, client: TestClient, admin_token: str):
        resp = client.post(
            "/api/v1/jobs",
            json={**SAMPLE_JOB, "title": "Admin-Created Job"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201

    def test_readonly_cannot_create_job(self, client: TestClient, readonly_token: str):
        resp = client.post(
            "/api/v1/jobs",
            json=SAMPLE_JOB,
            headers={"Authorization": f"Bearer {readonly_token}"},
        )
        assert resp.status_code == 403

    def test_unauthenticated_cannot_create_job(self, client: TestClient):
        resp = client.post("/api/v1/jobs", json=SAMPLE_JOB)
        assert resp.status_code == 401

    def test_missing_title_returns_422(self, client: TestClient, hr_token: str):
        resp = client.post(
            "/api/v1/jobs",
            json={**SAMPLE_JOB, "title": ""},
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        assert resp.status_code == 422


class TestListJobs:
    def test_any_auth_user_can_list_jobs(self, client: TestClient, readonly_token: str):
        resp = client.get(
            "/api/v1/jobs",
            headers={"Authorization": f"Bearer {readonly_token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_unauthenticated_cannot_list_jobs(self, client: TestClient):
        resp = client.get("/api/v1/jobs")
        assert resp.status_code == 401


class TestDeactivateJob:
    def test_admin_can_deactivate_job(self, client: TestClient, admin_token: str, hr_token: str):
        # Create a job first
        create_resp = client.post(
            "/api/v1/jobs",
            json={**SAMPLE_JOB, "title": "Job to Deactivate"},
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        assert create_resp.status_code == 201
        job_id = create_resp.json()["public_id"]

        # Deactivate as admin
        del_resp = client.delete(
            f"/api/v1/jobs/{job_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert del_resp.status_code == 200

    def test_hr_cannot_deactivate_job(self, client: TestClient, admin_token: str, hr_token: str):
        create_resp = client.post(
            "/api/v1/jobs",
            json={**SAMPLE_JOB, "title": "HR Cannot Delete"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert create_resp.status_code == 201
        job_id = create_resp.json()["public_id"]

        del_resp = client.delete(
            f"/api/v1/jobs/{job_id}",
            headers={"Authorization": f"Bearer {hr_token}"},
        )
        assert del_resp.status_code == 403
