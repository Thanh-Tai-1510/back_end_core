from typing import Annotated

from fastapi import APIRouter, status

from src.base.controllers.deps import AuthServiceDep, require_permission
from src.base.controllers.auth_controller import AuthController
from src.core.permissions import PermissionCode
from src.base.models.user import User
from src.base.requests.auth_request import LoginRequest, RegisterRequest
from src.base.responses.auth_response import TokenResponse
from src.base.responses.user_response import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])
controller = AuthController()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, auth_service: AuthServiceDep) -> UserResponse:
    return controller.register(request, auth_service)


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, auth_service: AuthServiceDep) -> TokenResponse:
    return controller.login(request, auth_service)


@router.get("/me", response_model=UserResponse)
def me(current_user: Annotated[User, require_permission(PermissionCode.AUTH_ME)]) -> UserResponse:
    return controller.me(current_user)
