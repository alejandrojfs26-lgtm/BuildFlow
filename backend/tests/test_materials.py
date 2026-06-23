import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_material(client: AsyncClient, auth_headers: dict[str, str]):
    resp = await client.post(
        "/api/v1/materials/",
        json={
            "name": "Cement",
            "unit": "kg",
            "unit_price": 5000,
            "stock": 1000,
            "min_stock": 100,
            "category": "Raw Materials",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Cement"
    assert data["unit"] == "kg"


@pytest.mark.asyncio
async def test_list_materials(client: AsyncClient, auth_headers: dict[str, str]):
    await client.post(
        "/api/v1/materials/", json={"name": "M1", "unit": "unit"},
        headers=auth_headers,
    )
    await client.post(
        "/api/v1/materials/", json={"name": "M2", "unit": "unit"},
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/materials/", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_material(client: AsyncClient, auth_headers: dict[str, str]):
    created = await client.post(
        "/api/v1/materials/", json={"name": "Get M", "unit": "kg"},
        headers=auth_headers,
    )
    mid = created.json()["id"]
    resp = await client.get(f"/api/v1/materials/{mid}", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_update_material(client: AsyncClient, auth_headers: dict[str, str]):
    created = await client.post(
        "/api/v1/materials/", json={"name": "Old", "unit": "kg", "stock": 50},
        headers=auth_headers,
    )
    mid = created.json()["id"]
    resp = await client.put(
        f"/api/v1/materials/{mid}",
        json={"name": "Updated", "stock": 200},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated"
    assert resp.json()["stock"] == 200


@pytest.mark.asyncio
async def test_delete_material(client: AsyncClient, auth_headers: dict[str, str]):
    created = await client.post(
        "/api/v1/materials/", json={"name": "Delete M", "unit": "unit"},
        headers=auth_headers,
    )
    mid = created.json()["id"]
    await client.delete(f"/api/v1/materials/{mid}", headers=auth_headers)
    resp = await client.get(f"/api/v1/materials/{mid}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_low_stock_filter(client: AsyncClient, auth_headers: dict[str, str]):
    await client.post(
        "/api/v1/materials/",
        json={"name": "Low", "unit": "unit", "stock": 5, "min_stock": 10},
        headers=auth_headers,
    )
    await client.post(
        "/api/v1/materials/",
        json={"name": "OK", "unit": "unit", "stock": 50, "min_stock": 10},
        headers=auth_headers,
    )
    resp = await client.get(
        "/api/v1/materials/?low_stock=true",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    names = [m["name"] for m in resp.json()]
    assert "Low" in names
    assert "OK" not in names


@pytest.mark.asyncio
async def test_tenant_isolation_materials(
    client: AsyncClient,
    auth_headers: dict[str, str],
    second_tenant_headers: dict[str, str],
):
    await client.post(
        "/api/v1/materials/", json={"name": "T1 Mat", "unit": "unit"},
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/materials/", headers=second_tenant_headers)
    assert len(resp.json()) == 0
