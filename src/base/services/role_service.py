from datetime import UTC, datetime

from sqlalchemy.orm import Session

from src.core.logging import Loggers, get_logger
from src.base.models.role import Role
from src.base.repositories.role_repository import RoleRepository
from src.base.requests.role_request import CreateRoleRequest, UpdateRoleRequest

logger = get_logger(Loggers.SERVICE)


class RoleService:
    def __init__(self, db: Session) -> None:
        self.repo = RoleRepository(db)

    def list_roles(self) -> list[Role]:
        return self.repo.list_all()

    def get_by_id(self, role_id: int) -> Role | None:
        role = self.repo.get_by_id(role_id)
        if role is None or role.is_deleted:
            return None
        return role

    def create(self, request: CreateRoleRequest) -> Role:
        if self.repo.code_exists(request.code):
            raise ValueError(f"Role code '{request.code}' already exists")

        role = Role(
            code=request.code,
            name=request.name,
            description=request.description,
            is_active=request.is_active,
            sort_order=request.sort_order,
        )
        self.repo.add(role)
        self.repo.commit()
        self.repo.refresh(role)
        logger.info("Role created: id=%s code=%s", role.id, role.code)
        return role

    def update(self, role: Role, request: UpdateRoleRequest) -> Role:
        data = request.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(role, field, value)
        self.repo.commit()
        self.repo.refresh(role)
        logger.info("Role updated: id=%s", role.id)
        return role

    def soft_delete(self, role: Role) -> None:
        if role.is_system:
            raise ValueError("Cannot delete system role")
        role.deleted_at = datetime.now(UTC).replace(tzinfo=None)
        role.is_active = False
        self.repo.commit()
        logger.info("Role soft-deleted: id=%s", role.id)
