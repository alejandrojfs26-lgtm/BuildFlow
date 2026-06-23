import pytest
from httpx import AsyncClient


@pytest.fixture
async def project_id(client: AsyncClient, auth_headers: dict[str, str]) -> str:
    c_resp = await client.post(
        "/api/v1/clients/", json={"name": "PM Client"}, headers=auth_headers
    )
    cid = c_resp.json()["id"]
    p_resp = await client.post(
        "/api/v1/projects/",
        json={"client_id": cid, "name": "PM Project", "code": "PM-PRJ"},
        headers=auth_headers,
    )
    return p_resp.json()["id"]


@pytest.fixture
async def material_id(client: AsyncClient, auth_headers: dict[str, str]) -> str:
    resp = await client.post(
        "/api/v1/materials/",
        json={"name": "Stock Mat", "unit": "unit", "stock": 100, "min_stock": 10},
        headers=auth_headers,
    )
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_project_material(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project_id: str,
    material_id: str,
):
    resp = await client.post(
        "/api/v1/project-materials/",
        json={
            "project_id": project_id,
            "material_id": material_id,
            "quantity": 10,
            "unit_price": 5000,
            "date": "2026-06-01",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["quantity"] == 10
    assert data["unit_price"] == 5000
    assert data["total_price"] == 50000


@pytest.mark.asyncio
async def test_insufficient_stock(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project_id: str,
    material_id: str,
):
    resp = await client.post(
        "/api/v1/project-materials/",
        json={
            "project_id": project_id,
            "material_id": material_id,
            "quantity": 9999,
            "unit_price": 100,
            "date": "2026-06-01",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_project_materials(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project_id: str,
    material_id: str,
):
    await client.post(
        "/api/v1/project-materials/",
        json={
            "project_id": project_id,
            "material_id": material_id,
            "quantity": 5,
            "unit_price": 1000,
            "date": "2026-06-01",
        },
        headers=auth_headers,
    )
    resp = await client.get(
        "/api/v1/project-materials/",
        params={"project_id": project_id},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1
