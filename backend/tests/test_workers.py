import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_worker(client: AsyncClient, auth_headers: dict[str, str]):
    resp = await client.post(
        "/api/v1/workers/",
        json={
            "full_name": "Juan Pérez",
            "dni": "12.345.678-9",
            "position": "Carpenter",
            "hourly_rate": 15000,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["full_name"] == "Juan Pérez"
    assert data["dni"] == "12.345.678-9"


@pytest.mark.asyncio
async def test_list_workers(client: AsyncClient, auth_headers: dict[str, str]):
    await client.post(
        "/api/v1/workers/", json={"full_name": "W1", "dni": "1"}, headers=auth_headers
    )
    await client.post(
        "/api/v1/workers/", json={"full_name": "W2", "dni": "2"}, headers=auth_headers
    )
    resp = await client.get("/api/v1/workers/", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_worker(client: AsyncClient, auth_headers: dict[str, str]):
    created = await client.post(
        "/api/v1/workers/", json={"full_name": "Find Me", "dni": "999"},
        headers=auth_headers,
    )
    wid = created.json()["id"]
    resp = await client.get(f"/api/v1/workers/{wid}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Find Me"


@pytest.mark.asyncio
async def test_update_worker(client: AsyncClient, auth_headers: dict[str, str]):
    created = await client.post(
        "/api/v1/workers/", json={"full_name": "Old Name", "dni": "888"},
        headers=auth_headers,
    )
    wid = created.json()["id"]
    resp = await client.put(
        f"/api/v1/workers/{wid}",
        json={"full_name": "New Name", "hourly_rate": 20000},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "New Name"
    assert resp.json()["hourly_rate"] == 20000


@pytest.mark.asyncio
async def test_delete_worker(client: AsyncClient, auth_headers: dict[str, str]):
    created = await client.post(
        "/api/v1/workers/", json={"full_name": "Delete Me", "dni": "777"},
        headers=auth_headers,
    )
    wid = created.json()["id"]
    await client.delete(f"/api/v1/workers/{wid}", headers=auth_headers)
    resp = await client.get(f"/api/v1/workers/{wid}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_dni(client: AsyncClient, auth_headers: dict[str, str]):
    await client.post(
        "/api/v1/workers/", json={"full_name": "First", "dni": "DUP-1"},
        headers=auth_headers,
    )
    resp = await client.post(
        "/api/v1/workers/", json={"full_name": "Second", "dni": "DUP-1"},
        headers=auth_headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_tenant_isolation_workers(
    client: AsyncClient,
    auth_headers: dict[str, str],
    second_tenant_headers: dict[str, str],
):
    await client.post(
        "/api/v1/workers/", json={"full_name": "T1 Worker", "dni": "ISO-1"},
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/workers/", headers=second_tenant_headers)
    assert len(resp.json()) == 0
