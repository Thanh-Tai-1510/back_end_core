from datetime import date

from pydantic import BaseModel, EmailStr, Field

from src.base.models.enums import Gender


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=8, max_length=128)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    display_name: str | None = Field(default=None, max_length=150)
    phone: str | None = Field(default=None, max_length=20)
    date_of_birth: date | None = None
    gender: Gender = Gender.UNSPECIFIED
    locale: str = Field(default="vi", max_length=10)
    timezone: str = Field(default="Asia/Ho_Chi_Minh", max_length=64)


class LoginRequest(BaseModel):
    username: str
    password: str
