from datetime import date

from pydantic import BaseModel, EmailStr, Field

from src.base.models.enums import Gender


class UpdateProfileRequest(BaseModel):
    email: EmailStr | None = None
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    display_name: str | None = Field(default=None, max_length=150)
    phone: str | None = Field(default=None, max_length=20)
    avatar_url: str | None = None
    bio: str | None = Field(default=None, max_length=2000)
    date_of_birth: date | None = None
    gender: Gender | None = None
    locale: str | None = Field(default=None, max_length=10)
    timezone: str | None = Field(default=None, max_length=64)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class AdminUpdateUserRequest(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(default=None, min_length=3, max_length=100)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    display_name: str | None = Field(default=None, max_length=150)
    phone: str | None = Field(default=None, max_length=20)
    avatar_url: str | None = None
    bio: str | None = None
    role_id: int | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    is_staff: bool | None = None
    is_verified: bool | None = None
    must_change_password: bool | None = None
