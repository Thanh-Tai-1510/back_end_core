from pydantic import BaseModel, Field, model_validator

PERMISSION_CODE_PATTERN = r"^[a-z0-9_.-]+(:[a-z0-9_.-]+)+$"


class CreatePermissionRequest(BaseModel):
    code: str = Field(max_length=100, pattern=PERMISSION_CODE_PATTERN, examples=["orders:read"])
    name: str = Field(min_length=1, max_length=150)
    module: str | None = Field(default=None, max_length=50, description="Default: part of code before the first ':'")
    action: str | None = Field(default=None, max_length=50, description="Default: rest of code after the first ':'")
    description: str | None = None
    is_active: bool = True

    @model_validator(mode="after")
    def _derive_module_action(self) -> "CreatePermissionRequest":
        module, _, action = self.code.partition(":")
        self.module = self.module or module
        self.action = self.action or action[:50]
        return self


class UpdatePermissionRequest(BaseModel):
    """`code` cannot change: application code and menus refer to it."""

    name: str | None = Field(default=None, min_length=1, max_length=150)
    module: str | None = Field(default=None, min_length=1, max_length=50)
    action: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = None
    is_active: bool | None = None
