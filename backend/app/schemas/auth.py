from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.core.constants import Role


class RegisterRequest(BaseModel):
    company_name: str
    company_slug: str
    email: EmailStr
    password: str
    full_name: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain an uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain a digit")
        return v

    @field_validator("company_slug")
    @classmethod
    def slug_format(cls, v: str) -> str:
        if not v.islower() or " " in v:
            raise ValueError("Slug must be lowercase without spaces")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserFromToken(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    email: str
    full_name: str
    role: Role
    is_active: bool
