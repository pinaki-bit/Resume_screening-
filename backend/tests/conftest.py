"""
backend/tests/conftest.py

Shared test fixtures.
Updated for v0.2.0: auth routes moved to /api/v1/auth/.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.security import hash_password
from app.database import Base, get_db
from app.main import create_app
from app.models.user import User

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = sessionmaker(
    bind=test_engine, autocommit=False, autoflush=False
)


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db_session(create_test_tables) -> Session:
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    app = create_app()

    # Seed test users (must_change_password=False for test stability)
    if not db_session.query(User).filter_by(email="test@example.com").first():
        db_session.add(User(
            email="test@example.com",
            hashed_password=hash_password("testpass123"),
            full_name="Test Admin",
            role="admin",
            is_active=True,
            is_admin=True,
            must_change_password=False,
        ))
    if not db_session.query(User).filter_by(email="hr@example.com").first():
        db_session.add(User(
            email="hr@example.com",
            hashed_password=hash_password("testpass123"),
            full_name="HR User",
            role="hr",
            is_active=True,
            is_admin=False,
            must_change_password=False,
        ))
    if not db_session.query(User).filter_by(email="readonly@example.com").first():
        db_session.add(User(
            email="readonly@example.com",
            hashed_password=hash_password("testpass123"),
            full_name="Read Only",
            role="readonly",
            is_active=True,
            is_admin=False,
            must_change_password=False,
        ))
    db_session.commit()

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture()
def admin_token(client: TestClient) -> str:
    """Return a valid admin JWT token."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture()
def hr_token(client: TestClient) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "hr@example.com", "password": "testpass123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture()
def readonly_token(client: TestClient) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "readonly@example.com", "password": "testpass123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]
