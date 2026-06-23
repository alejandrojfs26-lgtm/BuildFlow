import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_client(client: AsyncClient, auth_headers: dict[str, str]):
    resp = await client.post(
        "/api/v1/clients/",
        json={"name": "Acme Corp", "tax_id": "12345678-9", "email": "contact@acme.com"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Acme Corp"
    assert data["id"]


@pytest.mark.asyncio
async def test_list_clients(client: AsyncClient, auth_headers: dict[str, str]):
    await client.post("/api/v1/clients/", json={"name": "Client A"}, headers=auth_headers)
    await client.post("/api/v1/clients/", json={"name": "Client B"}, headers=auth_headers)
    resp = await client.get("/api/v1/clients/", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_client(client: AsyncClient, auth_headers: dict[str, str]):
    created = await client.post(
        "/api/v1/clients/", json={"name": "Get Me"}, headers=auth_headers
    )
    cid = created.json()["id"]
    resp = await client.get(f"/api/v1/clients/{cid}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Get Me"


@pytest.mark.asyncio
async def test_update_client(client: AsyncClient, auth_headers: dict[str, str]):
    created = await client.post(
        "/api/v1/clients/", json={"name": "Old Name"}, headers=auth_headers
    )
    cid = created.json()["id"]
    resp = await client.put(
        f"/api/v1/clients/{cid}",
        json={"name": "New Name"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_client(client: AsyncClient, auth_headers: dict[str, str]):
    created = await client.post(
        "/api/v1/clients/", json={"name": "Delete Me"}, headers=auth_headers
    )
    cid = created.json()["id"]
    resp = await client.delete(f"/api/v1/clients/{cid}", headers=auth_headers)
    assert resp.status_code == 200
    get_resp = await client.get(f"/api/v1/clients/{cid}", headers=auth_headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_tenant_isolation_clients(
    client: AsyncClient, auth_headers: dict[str, str], second_tenant_headers: dict[str, str]
):
    await client.post("/api/v1/clients/", json={"name": "Tenant A Client"}, headers=auth_headers)
    resp = await client.get("/api/v1/clients/", headers=second_tenant_headers)
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_client_not_found(client: AsyncClient, auth_headers: dict[str, str]):
    resp = await client.get(
        "/api/v1/clients/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert resp.status_code == 404
