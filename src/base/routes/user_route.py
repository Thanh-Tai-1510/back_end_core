from typing import Annotated

from fastapi import APIRouter, status

from src.base.controllers.deps import UserServiceDep, require_permission
from src.base.controllers.user_controller import UserController
from src.core.permissions import PermissionCode
from src.base.models.user import User
from src.base.requests.user_request import ChangePasswordRequest, UpdateProfileRequest
from src.base.responses.user_response import UserResponse

router = APIRouter(prefix="/users", tags=["users"])
controller = UserController()


@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: Annotated[User, require_permission(PermissionCode.USERS_ME_READ)],
) -> UserResponse:
    return controller.get_my_profile(current_user)


@router.patch("/me", response_model=UserResponse)
def update_my_profile(
    request: UpdateProfileRequest,
    current_user: Annotated[User, require_permission(PermissionCode.USERS_ME_UPDATE)],
    user_service: UserServiceDep,
) -> UserResponse:
    return controller.update_my_profile(request, current_user, user_service)


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_my_password(
    request: ChangePasswordRequest,
    current_user: Annotated[User, require_permission(PermissionCode.USERS_ME_CHANGE_PASSWORD)],
    user_service: UserServiceDep,
) -> None:
    controller.change_my_password(request, current_user, user_service)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_account(
    current_user: Annotated[User, require_permission(PermissionCode.USERS_ME_DELETE)],
    user_service: UserServiceDep,
) -> None:
    controller.delete_my_account(current_user, user_service)
