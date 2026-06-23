import uuid
from collections.abc import Generator
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import JSON, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.types import TypeDecorator

from app.db.base import Base
from app.db.session import get_db
from app.main import app

TEST_DB_FILE = "/tmp/buildflow_test.db"
TEST_DB_URL = f"sqlite:///{TEST_DB_FILE}"


class _JSONB(TypeDecorator):
    impl = JSON
    cache_ok = True

for mapper in Base.registry.mappers:
    for col in mapper.columns:
        if isinstance(col.type, JSONB):
            col.type = _JSONB()


@pytest.fixture(scope="session")
def test_engine():
    import os

    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)

    engine = create_engine(TEST_DB_URL, echo=False)

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)


@pytest.fixture
def db_session(test_engine) -> Generator[Session, Any]:
    test_session_local = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
    session = test_session_local()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def override_db(test_app: FastAPI, db_session: Session) -> FastAPI:
    def _get_db():
        yield db_session

    test_app.dependency_overrides[get_db] = _get_db
    return test_app


@pytest.fixture
def test_app() -> FastAPI:
    return app


@pytest.fixture
async def client(override_db: FastAPI) -> AsyncClient:
    transport = ASGITransport(app=override_db)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    slug = f"test-{uuid.uuid4().hex[:8]}"
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "company_name": "Test Corp",
            "company_slug": slug,
            "email": f"admin@{slug}.com",
            "password": "testpass123",
            "full_name": "Admin User",
        },
    )
    data = resp.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest.fixture
async def second_tenant_headers(client: AsyncClient) -> dict[str, str]:
    slug = f"other-{uuid.uuid4().hex[:8]}"
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "company_name": "Other Corp",
            "company_slug": slug,
            "email": f"admin@{slug}.com",
            "password": "testpass123",
            "full_name": "Other Admin",
        },
    )
    data = resp.json()
    return {"Authorization": f"Bearer {data['access_token']}"}
