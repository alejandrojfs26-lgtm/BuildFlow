from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.core.constants import Role


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Role = Role.WORKER


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    email: str
    full_name: str
    role: Role
    is_active: bool
    phone: str | None = None
