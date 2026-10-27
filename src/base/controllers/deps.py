from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.logging import Loggers, get_logger
from src.core.security import decode_access_token
from src.base.models.user import User
from src.base.repositories.user_repository import UserRepository
from src.base.services.auth_service import AuthService
from src.base.services.chat_service import ChatService
from src.base.services.config_service import ConfigService
from src.base.services.menu_service import MenuService
from src.base.services.permission_service import PermissionService
from src.base.services.role_service import RoleService
from src.base.services.user_service import UserService

bearer_scheme = HTTPBearer()
logger = get_logger(Loggers.AUTH)

DbSession = Annotated[Session, Depends(get_db)]


def get_config_service(db: DbSession) -> ConfigService:
    return ConfigService(db)


def get_user_service(db: DbSession) -> UserService:
    return UserService(db)


def get_auth_service(db: DbSession, config: ConfigService = Depends(get_config_service)) -> AuthService:
    return AuthService(db, config)


def get_role_service(db: DbSession) -> RoleService:
    return RoleService(db)


def get_menu_service(db: DbSession) -> MenuService:
    return MenuService(db)


def get_permission_service(db: DbSession) -> PermissionService:
    return PermissionService(db)


def get_chat_service(config: ConfigService = Depends(get_config_service)) -> ChatService:
    return ChatService(config)


ConfigDep = Annotated[ConfigService, Depends(get_config_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
RoleServiceDep = Annotated[RoleService, Depends(get_role_service)]
MenuServiceDep = Annotated[MenuService, Depends(get_menu_service)]
PermissionServiceDep = Annotated[PermissionService, Depends(get_permission_service)]
ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]


def get_current_user(
    db: DbSession,
    config: ConfigDep,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> User:
    payload = decode_access_token(
        credentials.credentials,
        secret_key=config.get_jwt_secret_key(),
        algorithm=config.get_jwt_algorithm(),
    )
    if payload is None or payload.get("sub") is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ",
        )

    user = UserRepository(db).get_by_id(int(payload["sub"]))
    if user is None or user.is_deleted or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ",
        )
    return user


def require_permission(permission_code: str):
    def dependency(
        current_user: Annotated[User, Depends(get_current_user)],
        permission_service: PermissionServiceDep,
    ) -> User:
        if not permission_service.has_permission(current_user, permission_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Không có quyền thực hiện thao tác này",
            )
        return current_user

    return Depends(dependency)


CurrentUser = Annotated[User, Depends(get_current_user)]
