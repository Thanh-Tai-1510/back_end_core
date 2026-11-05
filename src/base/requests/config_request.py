from pydantic import BaseModel, Field

CONFIG_KEY_PATTERN = r"^[A-Za-z0-9_.:-]{1,150}$"


class CreateConfigRequest(BaseModel):
    key: str = Field(pattern=CONFIG_KEY_PATTERN, examples=["app_name"])
    type: str | None = Field(default=None, max_length=50, description="Group name, e.g. app, auth, mail")
    value: str | None = None


class UpdateConfigRequest(BaseModel):
    type: str | None = Field(default=None, max_length=50)
    value: str | None = None
