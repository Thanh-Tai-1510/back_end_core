from pydantic import BaseModel, Field


class CreateConfigRequest(BaseModel):
    key: str = Field(min_length=1, max_length=255)
    type: str | None = Field(default=None, max_length=100)
    value: str | None = None


class UpdateConfigRequest(BaseModel):
    type: str | None = Field(default=None, max_length=100)
    value: str | None = None
