import pytest
from httpx import AsyncClient


@pytest.fixture
async def project_id(client: AsyncClient, auth_headers: dict[str, str]) -> str:
    c_resp = await client.post(
        "/api/v1/clients/", json={"name": "Assn Client"}, headers=auth_headers
    )
    cid = c_resp.json()["id"]
    p_resp = await client.post(
        "/api/v1/projects/",
        json={"client_id": cid, "name": "Assn Project", "code": "ASS-PRJ"},
        headers=auth_headers,
    )
    return p_resp.json()["id"]


@pytest.fixture
async def worker_id(client: AsyncClient, auth_headers: dict[str, str]) -> str:
    resp = await client.post(
        "/api/v1/workers/", json={"full_name": "Assn Worker", "dni": "ASS-W"},
        headers=auth_headers,
    )
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_assignment(
    client: AsyncClient, auth_headers: dict[str, str], project_id: str, worker_id: str
):
    resp = await client.post(
        "/api/v1/assignments/",
        json={
            "project_id": project_id,
            "worker_id": worker_id,
            "role": "Carpenter",
            "start_date": "2026-06-01",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["project_id"] == project_id
    assert data["worker_id"] == worker_id


@pytest.mark.asyncio
async def test_list_assignments(
    client: AsyncClient, auth_headers: dict[str, str], project_id: str, worker_id: str
):
    await client.post(
        "/api/v1/assignments/",
        json={"project_id": project_id, "worker_id": worker_id, "start_date": "2026-06-01"},
        headers=auth_headers,
    )
    resp = await client.get(
        "/api/v1/assignments/",
        params={"project_id": project_id},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_get_assignment(
    client: AsyncClient, auth_headers: dict[str, str], project_id: str, worker_id: str
):
    created = await client.post(
        "/api/v1/assignments/",
        json={"project_id": project_id, "worker_id": worker_id, "start_date": "2026-06-01"},
        headers=auth_headers,
    )
    aid = created.json()["id"]
    resp = await client.get(f"/api/v1/assignments/{aid}", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_delete_assignment(
    client: AsyncClient, auth_headers: dict[str, str], project_id: str, worker_id: str
):
    created = await client.post(
        "/api/v1/assignments/",
        json={"project_id": project_id, "worker_id": worker_id, "start_date": "2026-06-01"},
        headers=auth_headers,
    )
    aid = created.json()["id"]
    await client.delete(f"/api/v1/assignments/{aid}", headers=auth_headers)
    resp = await client.get(f"/api/v1/assignments/{aid}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_assignment(
    client: AsyncClient, auth_headers: dict[str, str], project_id: str, worker_id: str
):
    await client.post(
        "/api/v1/assignments/",
        json={"project_id": project_id, "worker_id": worker_id, "start_date": "2026-06-01"},
        headers=auth_headers,
    )
    resp = await client.post(
        "/api/v1/assignments/",
        json={"project_id": project_id, "worker_id": worker_id, "start_date": "2026-06-01"},
        headers=auth_headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_tenant_isolation_assignments(
    client: AsyncClient,
    auth_headers: dict[str, str],
    second_tenant_headers: dict[str, str],
    project_id: str,
    worker_id: str,
):
    await client.post(
        "/api/v1/assignments/",
        json={"project_id": project_id, "worker_id": worker_id, "start_date": "2026-06-01"},
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/assignments/", headers=second_tenant_headers)
    assert len(resp.json()) == 0
