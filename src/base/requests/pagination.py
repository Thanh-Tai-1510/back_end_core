from pydantic import BaseModel, Field


class PageParams(BaseModel):
    """Query params ?page=&page_size=. Use via base.controllers.deps.PageParamsDep."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=200)

    @property
    def limit(self) -> int:
        return self.page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
