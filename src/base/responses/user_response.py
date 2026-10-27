from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from src.base.models.enums import AuthProvider, Gender
from src.base.models.user import User
from src.base.responses.role_response import RoleBriefResponse


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    public_id: UUID
    email: EmailStr
    username: str
    first_name: str | None
    last_name: str | None
    display_name: str | None
    full_name: str | None = None
    phone: str | None
    avatar_url: str | None
    bio: str | None
    date_of_birth: date | None
    gender: Gender
    role_id: int
    role: RoleBriefResponse
    locale: str
    timezone: str
    is_active: bool
    is_superuser: bool
    is_staff: bool
    is_verified: bool
    email_verified_at: datetime | None
    must_change_password: bool
    last_login_at: datetime | None
    auth_provider: AuthProvider
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, user: User) -> "UserResponse":
        return cls.model_validate(user)


class UserPublicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    username: str
    display_name: str | None
    full_name: str | None = None
    avatar_url: str | None
    bio: str | None
    role: RoleBriefResponse

    @classmethod
    def from_model(cls, user: User) -> "UserPublicResponse":
        return cls.model_validate(user)
