import pytest
from httpx import AsyncClient


@pytest.fixture
async def client_id(client: AsyncClient, auth_headers: dict[str, str]) -> str:
    resp = await client.post(
        "/api/v1/clients/", json={"name": "Project Client"}, headers=auth_headers
    )
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_project(
    client: AsyncClient, auth_headers: dict[str, str], client_id: str
):
    resp = await client.post(
        "/api/v1/projects/",
        json={
            "client_id": client_id,
            "name": "New Project",
            "code": "PRJ-001",
            "budget": 100000,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "New Project"
    assert data["code"] == "PRJ-001"
    assert data["status"] == "planning"


@pytest.mark.asyncio
async def test_list_projects(
    client: AsyncClient, auth_headers: dict[str, str], client_id: str
):
    await client.post(
        "/api/v1/projects/",
        json={"client_id": client_id, "name": "P1", "code": "P-001"},
        headers=auth_headers,
    )
    await client.post(
        "/api/v1/projects/",
        json={"client_id": client_id, "name": "P2", "code": "P-002"},
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/projects/", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_project(
    client: AsyncClient, auth_headers: dict[str, str], client_id: str
):
    created = await client.post(
        "/api/v1/projects/",
        json={"client_id": client_id, "name": "Get P", "code": "P-GET"},
        headers=auth_headers,
    )
    pid = created.json()["id"]
    resp = await client.get(f"/api/v1/projects/{pid}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Get P"


@pytest.mark.asyncio
async def test_update_project(
    client: AsyncClient, auth_headers: dict[str, str], client_id: str
):
    created = await client.post(
        "/api/v1/projects/",
        json={"client_id": client_id, "name": "Old", "code": "P-OLD"},
        headers=auth_headers,
    )
    pid = created.json()["id"]
    resp = await client.put(
        f"/api/v1/projects/{pid}",
        json={"name": "Updated", "budget": 50000},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated"
    assert resp.json()["budget"] == 50000


@pytest.mark.asyncio
async def test_delete_project(
    client: AsyncClient, auth_headers: dict[str, str], client_id: str
):
    created = await client.post(
        "/api/v1/projects/",
        json={"client_id": client_id, "name": "Delete P", "code": "P-DEL"},
        headers=auth_headers,
    )
    pid = created.json()["id"]
    await client.delete(f"/api/v1/projects/{pid}", headers=auth_headers)
    resp = await client.get(f"/api/v1/projects/{pid}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_code(
    client: AsyncClient, auth_headers: dict[str, str], client_id: str
):
    await client.post(
        "/api/v1/projects/",
        json={"client_id": client_id, "name": "First", "code": "DUP"},
        headers=auth_headers,
    )
    resp = await client.post(
        "/api/v1/projects/",
        json={"client_id": client_id, "name": "Second", "code": "DUP"},
        headers=auth_headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_tenant_isolation_projects(
    client: AsyncClient,
    auth_headers: dict[str, str],
    second_tenant_headers: dict[str, str],
    client_id: str,
):
    await client.post(
        "/api/v1/projects/",
        json={"client_id": client_id, "name": "T1 Project", "code": "T1-P"},
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/projects/", headers=second_tenant_headers)
    assert len(resp.json()) == 0
