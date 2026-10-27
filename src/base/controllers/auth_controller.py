from fastapi import HTTPException, status

from src.base.controllers.deps import AuthServiceDep
from src.core.logging import Loggers, get_logger
from src.base.requests.auth_request import LoginRequest, RegisterRequest
from src.base.responses.auth_response import TokenResponse
from src.base.responses.user_response import UserResponse

logger = get_logger(Loggers.AUTH)


class AuthController:
    def register(self, request: RegisterRequest, auth_service: AuthServiceDep) -> UserResponse:
        try:
            user = auth_service.register(request)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        return UserResponse.from_model(user)

    def login(self, request: LoginRequest, auth_service: AuthServiceDep) -> TokenResponse:
        try:
            return auth_service.login(request)
        except ValueError as exc:
            error = str(exc)
            if error == "invalid_credentials":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Sai username hoặc mật khẩu",
                ) from exc
            if error == "account_locked":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Tài khoản bị khóa tạm thời",
                ) from exc
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tài khoản không hoạt động",
            ) from exc

    def me(self, current_user) -> UserResponse:
        return UserResponse.from_model(current_user)
