"""Auth API integration tests — verify HTTP contracts and auth enforcement.
"""

import pytest
from httpx import AsyncClient


REGISTER_PAYLOAD = {
    "company_name": "ApiTestCo",
    "company_slug": "apitestco",
    "email": "admin@apitestco.com",
    "password": "Str0ng!Pass1",
    "full_name": "Admin User",
}


class TestRegister:
    @pytest.mark.asyncio
    async def test_register_201(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email_409(
        self, client: AsyncClient
    ) -> None:
        await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
        resp = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_register_weak_password_422(
        self, client: AsyncClient
    ) -> None:
        payload = {**REGISTER_PAYLOAD, "password": "123"}
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_fields_422(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post("/api/v1/auth/register", json={})
        assert resp.status_code == 422


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_200(self, client: AsyncClient) -> None:
        await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
        resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": REGISTER_PAYLOAD["email"],
                "password": REGISTER_PAYLOAD["password"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_login_wrong_password_401(
        self, client: AsyncClient
    ) -> None:
        await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
        resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": REGISTER_PAYLOAD["email"],
                "password": "wrong-password",
            },
        )
        assert resp.status_code == 401


class TestMe:
    @pytest.mark.asyncio
    async def test_me_200(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        resp = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] is not None
        assert "password_hash" not in data

    @pytest.mark.asyncio
    async def test_me_422_no_auth_header(self, client: AsyncClient) -> None:
        """FastAPI returns 422 when a required Header param is missing."""
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_me_401_bearer_no_token(self, client: AsyncClient) -> None:
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer "},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_me_401_bad_token(self, client: AsyncClient) -> None:
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalidtoken"},
        )
        assert resp.status_code == 401


class TestRefresh:
    @pytest.mark.asyncio
    async def test_refresh_200(self, client: AsyncClient) -> None:
        await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": REGISTER_PAYLOAD["email"],
                "password": REGISTER_PAYLOAD["password"],
            },
        )
        refresh_token = login_resp.json()["refresh_token"]

        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_refresh_revokes_old(self, client: AsyncClient) -> None:
        await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": REGISTER_PAYLOAD["email"],
                "password": REGISTER_PAYLOAD["password"],
            },
        )
        old_token = login_resp.json()["refresh_token"]

        await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_token},
        )
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_token},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_invalid_token_401(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        assert resp.status_code == 401


class TestLogout:
    @pytest.mark.asyncio
    async def test_logout_200(self, client: AsyncClient) -> None:
        await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": REGISTER_PAYLOAD["email"],
                "password": REGISTER_PAYLOAD["password"],
            },
        )
        token = login_resp.json()["refresh_token"]

        resp = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": token},
        )
        assert resp.status_code == 200

        refresh_resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": token},
        )
        assert refresh_resp.status_code == 401
