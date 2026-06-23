from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.middleware.rate_limit import rate_limiter
from app.models.user import User
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.tenant import TenantRepository
from app.repositories.user import UserRepository
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserFromToken,
)
from app.schemas.common import Message
from app.services.auth import AuthService

router = APIRouter()


def _build_auth_service(db: Session) -> AuthService:
    return AuthService(
        UserRepository(db),
        TenantRepository(db),
        RefreshTokenRepository(db),
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    summary="Register a new company with admin user",
)
def register(data: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    rate_limiter.check(f"register:{ip}", max_attempts=3, window_seconds=3600)
    service = _build_auth_service(db)
    access, refresh, _ = service.register(data)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and get tokens",
)
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    rate_limiter.check(f"login:{ip}", max_attempts=10, window_seconds=300)
    service = _build_auth_service(db)
    access, refresh, _ = service.login(data.email, data.password)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Obtain new access token using refresh token",
)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    service = _build_auth_service(db)
    access, new_refresh = service.refresh(data.refresh_token)
    return TokenResponse(access_token=access, refresh_token=new_refresh)


@router.post(
    "/logout",
    response_model=Message,
    summary="Revoke refresh token",
)
def logout(data: RefreshRequest, db: Session = Depends(get_db)):
    service = _build_auth_service(db)
    service.logout(data.refresh_token)
    return Message(message="Logged out successfully")


@router.get(
    "/me",
    response_model=UserFromToken,
    summary="Get current authenticated user",
)
def me(current_user: User = Depends(get_current_user)):
    return UserFromToken.model_validate(current_user)
