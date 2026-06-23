import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "company_name": "New Co",
            "company_slug": "new-co",
            "email": "admin@newco.com",
            "password": "securepass123",
            "full_name": "New Admin",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    slug = "dup-email"
    await client.post(
        "/api/v1/auth/register",
        json={
            "company_name": "First",
            "company_slug": slug,
            "email": "dup@test.com",
            "password": "securepass123",
            "full_name": "Admin",
        },
    )
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "company_name": "Second",
            "company_slug": "second-co",
            "email": "dup@test.com",
            "password": "securepass123",
            "full_name": "Admin",
        },
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_register_duplicate_slug(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={
            "company_name": "First",
            "company_slug": "dupslug",
            "email": "first@test.com",
            "password": "securepass123",
            "full_name": "Admin",
        },
    )
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "company_name": "Second",
            "company_slug": "dupslug",
            "email": "second@test.com",
            "password": "securepass123",
            "full_name": "Admin",
        },
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "company_name": "Weak",
            "company_slug": "weak-co",
            "email": "weak@test.com",
            "password": "short",
            "full_name": "Admin",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    slug = "login-test"
    await client.post(
        "/api/v1/auth/register",
        json={
            "company_name": "Login Co",
            "company_slug": slug,
            "email": f"admin@{slug}.com",
            "password": "securepass123",
            "full_name": "Admin",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": f"admin@{slug}.com", "password": "securepass123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"]
    assert data["refresh_token"]


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@test.com", "password": "wrong"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me(client: AsyncClient, auth_headers: dict[str, str]):
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"]
    assert data["full_name"] == "Admin User"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_me_unauthorized(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_refresh(client: AsyncClient):
    slug = "refresh-test"
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "company_name": "Refresh Co",
            "company_slug": slug,
            "email": f"admin@{slug}.com",
            "password": "securepass123",
            "full_name": "Admin",
        },
    )
    refresh_token = reg.json()["refresh_token"]
    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"]
    assert data["refresh_token"]


@pytest.mark.asyncio
async def test_refresh_revokes_old(client: AsyncClient):
    slug = "refresh-revoke"
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "company_name": "Revoke Co",
            "company_slug": slug,
            "email": f"admin@{slug}.com",
            "password": "securepass123",
            "full_name": "Admin",
        },
    )
    old_refresh = reg.json()["refresh_token"]
    await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": old_refresh}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    slug = "logout-test"
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "company_name": "Logout Co",
            "company_slug": slug,
            "email": f"admin@{slug}.com",
            "password": "securepass123",
            "full_name": "Admin",
        },
    )
    refresh_token = reg.json()["refresh_token"]
    resp = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Logged out successfully"
    resp2 = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert resp2.status_code == 401
