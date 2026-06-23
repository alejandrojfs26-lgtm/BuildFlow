import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_empty(client: AsyncClient, auth_headers: dict[str, str]):
    resp = await client.get("/api/v1/dashboard/", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["projects"]["total"] == 0
    assert data["workers"]["total"] == 0
    assert data["materials"]["low_stock"] == 0
    assert data["clients"] == 0
    assert data["kpis"]["active_assignments"] == 0


@pytest.mark.asyncio
async def test_dashboard_with_data(
    client: AsyncClient, auth_headers: dict[str, str]
):
    c_resp = await client.post(
        "/api/v1/clients/", json={"name": "Dash Client"}, headers=auth_headers
    )
    cid = c_resp.json()["id"]
    await client.post(
        "/api/v1/projects/",
        json={"client_id": cid, "name": "Dash P", "code": "DASH-P"},
        headers=auth_headers,
    )
    await client.post(
        "/api/v1/workers/",
        json={"full_name": "Dash W", "dni": "DASH-W"},
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/dashboard/", headers=auth_headers)
    data = resp.json()
    assert data["projects"]["total"] == 1
    assert data["workers"]["total"] == 1
    assert data["clients"] == 1


@pytest.mark.asyncio
async def test_dashboard_tenant_isolation(
    client: AsyncClient,
    auth_headers: dict[str, str],
    second_tenant_headers: dict[str, str],
):
    c_resp = await client.post(
        "/api/v1/clients/", json={"name": "Isol Client"}, headers=auth_headers
    )
    cid = c_resp.json()["id"]
    await client.post(
        "/api/v1/projects/",
        json={"client_id": cid, "name": "Isol P", "code": "ISOL-P"},
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/dashboard/", headers=second_tenant_headers)
    assert resp.json()["projects"]["total"] == 0
