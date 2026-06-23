import pytest
from httpx import AsyncClient


@pytest.fixture
async def project_id(client: AsyncClient, auth_headers: dict[str, str]) -> str:
    c_resp = await client.post(
        "/api/v1/clients/", json={"name": "DR Client"}, headers=auth_headers
    )
    cid = c_resp.json()["id"]
    p_resp = await client.post(
        "/api/v1/projects/",
        json={"client_id": cid, "name": "DR Project", "code": "DR-PRJ"},
        headers=auth_headers,
    )
    return p_resp.json()["id"]


@pytest.fixture
async def worker_id(client: AsyncClient, auth_headers: dict[str, str]) -> str:
    resp = await client.post(
        "/api/v1/workers/", json={"full_name": "DR Worker", "dni": "DR-W"},
        headers=auth_headers,
    )
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_daily_report(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project_id: str,
    worker_id: str,
):
    resp = await client.post(
        "/api/v1/daily-reports/",
        json={
            "project_id": project_id,
            "worker_id": worker_id,
            "date": "2026-06-22",
            "hours_worked": 8,
            "description": "Worked on foundation",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["hours_worked"] == 8
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_list_daily_reports(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project_id: str,
    worker_id: str,
):
    await client.post(
        "/api/v1/daily-reports/",
        json={
            "project_id": project_id,
            "worker_id": worker_id,
            "date": "2026-06-22",
            "hours_worked": 8,
            "description": "Test",
        },
        headers=auth_headers,
    )
    resp = await client.get(
        "/api/v1/daily-reports/",
        params={"project_id": project_id},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_duplicate_daily_report(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project_id: str,
    worker_id: str,
):
    payload = {
        "project_id": project_id,
        "worker_id": worker_id,
        "date": "2026-06-22",
        "hours_worked": 8,
        "description": "First",
    }
    await client.post("/api/v1/daily-reports/", json=payload, headers=auth_headers)
    resp = await client.post(
        "/api/v1/daily-reports/", json=payload, headers=auth_headers
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_submit_daily_report(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project_id: str,
    worker_id: str,
):
    created = await client.post(
        "/api/v1/daily-reports/",
        json={
            "project_id": project_id,
            "worker_id": worker_id,
            "date": "2026-06-22",
            "hours_worked": 8,
            "description": "Submit test",
        },
        headers=auth_headers,
    )
    rid = created.json()["id"]
    resp = await client.post(
        f"/api/v1/daily-reports/{rid}/submit",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "submitted"


@pytest.mark.asyncio
async def test_approve_daily_report(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project_id: str,
    worker_id: str,
):
    created = await client.post(
        "/api/v1/daily-reports/",
        json={
            "project_id": project_id,
            "worker_id": worker_id,
            "date": "2026-06-22",
            "hours_worked": 8,
            "description": "Approve test",
        },
        headers=auth_headers,
    )
    rid = created.json()["id"]
    await client.post(f"/api/v1/daily-reports/{rid}/submit", headers=auth_headers)
    resp = await client.post(
        f"/api/v1/daily-reports/{rid}/approve",
        params={"notes": "Good work"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"
    assert resp.json()["notes"] == "Good work"


@pytest.mark.asyncio
async def test_reject_daily_report(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project_id: str,
    worker_id: str,
):
    created = await client.post(
        "/api/v1/daily-reports/",
        json={
            "project_id": project_id,
            "worker_id": worker_id,
            "date": "2026-06-22",
            "hours_worked": 8,
            "description": "Reject test",
        },
        headers=auth_headers,
    )
    rid = created.json()["id"]
    await client.post(f"/api/v1/daily-reports/{rid}/submit", headers=auth_headers)
    resp = await client.post(
        f"/api/v1/daily-reports/{rid}/reject",
        params={"notes": "Missing details"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"


@pytest.mark.asyncio
async def test_invalid_status_transition(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project_id: str,
    worker_id: str,
):
    created = await client.post(
        "/api/v1/daily-reports/",
        json={
            "project_id": project_id,
            "worker_id": worker_id,
            "date": "2026-06-22",
            "hours_worked": 8,
            "description": "Bad transition",
        },
        headers=auth_headers,
    )
    rid = created.json()["id"]
    resp = await client.post(
        f"/api/v1/daily-reports/{rid}/approve",
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_tenant_isolation_daily_reports(
    client: AsyncClient,
    auth_headers: dict[str, str],
    second_tenant_headers: dict[str, str],
    project_id: str,
    worker_id: str,
):
    await client.post(
        "/api/v1/daily-reports/",
        json={
            "project_id": project_id,
            "worker_id": worker_id,
            "date": "2026-06-22",
            "hours_worked": 8,
            "description": "T1 Report",
        },
        headers=auth_headers,
    )
    resp = await client.get(
        "/api/v1/daily-reports/", headers=second_tenant_headers
    )
    assert len(resp.json()) == 0
