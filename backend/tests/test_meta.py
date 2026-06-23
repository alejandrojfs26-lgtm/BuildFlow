
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_openapi_docs(client: AsyncClient):
    resp = await client.get("/docs")
    assert resp.status_code == 200
    assert "swagger" in resp.text.lower()


@pytest.mark.asyncio
async def test_redoc_docs(client: AsyncClient):
    resp = await client.get("/redoc")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_openapi_json(client: AsyncClient):
    resp = await client.get("/openapi.json")
    assert resp.status_code == 200
    spec = resp.json()
    assert spec["info"]["title"] == "BuildFlow"
    assert any(p.startswith("/api/v1") for p in spec["paths"])
