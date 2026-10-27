from sqlalchemy.orm import Session

from src.core.logging import Loggers, get_logger
from src.core.security import create_access_token
from src.base.models.user import User
from src.base.requests.auth_request import LoginRequest, RegisterRequest
from src.base.responses.auth_response import TokenResponse
from src.base.services.config_service import ConfigService
from src.base.services.user_service import UserService

logger = get_logger(Loggers.SERVICE)


class AuthService:
    def __init__(self, db: Session, config_service: ConfigService) -> None:
        self.user_service = UserService(db)
        self.config_service = config_service

    def register(self, request: RegisterRequest) -> User:
        return self.user_service.create(request)

    def login(self, request: LoginRequest) -> TokenResponse:
        user = self.user_service.authenticate(request.username, request.password)
        self.user_service.record_login_success(user)
        logger.info("Login success: user id=%s", user.id)
        return TokenResponse(
            access_token=create_access_token(
                subject=user.id,
                secret_key=self.config_service.get_jwt_secret_key(),
                algorithm=self.config_service.get_jwt_algorithm(),
                expires_minutes=self.config_service.get_jwt_expire_minutes(),
            )
        )
