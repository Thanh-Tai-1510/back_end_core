from fastapi import HTTPException, status

from src.base.controllers.deps import UserServiceDep
from src.core.logging import Loggers, get_logger
from src.base.requests.user_request import ChangePasswordRequest, UpdateProfileRequest
from src.base.responses.user_response import UserResponse

logger = get_logger(Loggers.API)


class UserController:
    def get_my_profile(self, current_user) -> UserResponse:
        return UserResponse.from_model(current_user)

    def update_my_profile(
        self,
        request: UpdateProfileRequest,
        current_user,
        user_service: UserServiceDep,
    ) -> UserResponse:
        try:
            user = user_service.update_profile(current_user, request)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        return UserResponse.from_model(user)

    def change_my_password(
        self,
        request: ChangePasswordRequest,
        current_user,
        user_service: UserServiceDep,
    ) -> None:
        try:
            user_service.change_password(current_user, request)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        logger.info("Password changed: user id=%s", current_user.id)

    def delete_my_account(self, current_user, user_service: UserServiceDep) -> None:
        user_service.soft_delete(current_user, actor=current_user)
        logger.info("Account soft-deleted: user id=%s", current_user.id)
