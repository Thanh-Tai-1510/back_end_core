from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from src.core.logging import Loggers, get_logger
from src.core.security import get_password_hash, verify_password
from src.base.models.user import User
from src.base.repositories.role_repository import RoleRepository
from src.base.repositories.user_repository import UserRepository
from src.base.requests.auth_request import RegisterRequest
from src.base.requests.user_request import AdminUpdateUserRequest, ChangePasswordRequest, UpdateProfileRequest

logger = get_logger(Loggers.SERVICE)

MAX_FAILED_LOGIN_ATTEMPTS = 5
LOCK_DURATION_MINUTES = 15


class UserService:
    def __init__(self, db: Session) -> None:
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)

    def get_by_id(self, user_id: int, *, include_deleted: bool = False) -> User | None:
        user = self.user_repo.get_by_id(user_id)
        if user is None or (user.is_deleted and not include_deleted):
            return None
        return user

    def get_by_username_or_email(self, identifier: str) -> User | None:
        return self.user_repo.get_by_username_or_email(identifier)

    def create(self, request: RegisterRequest) -> User:
        existing = self.user_repo.find_registration_conflict(
            request.email,
            request.username,
            request.phone,
        )
        if existing:
            raise ValueError("Email, username, or phone already registered")

        default_role = self.role_repo.get_default_user_role()
        if default_role is None:
            raise ValueError("Default role 'user' is not configured")

        now = datetime.now(UTC).replace(tzinfo=None)
        user = User(
            email=request.email,
            username=request.username,
            hashed_password=get_password_hash(request.password),
            first_name=request.first_name,
            last_name=request.last_name,
            display_name=request.display_name or request.username,
            phone=request.phone,
            date_of_birth=request.date_of_birth,
            gender=request.gender,
            locale=request.locale,
            timezone=request.timezone,
            role_id=default_role.id,
            password_changed_at=now,
        )
        self.user_repo.add(user)
        self.user_repo.commit()
        self.user_repo.refresh(user, attribute_names=["role"])
        logger.info("User created: id=%s username=%s", user.id, user.username)
        return user

    def update_profile(self, user: User, request: UpdateProfileRequest) -> User:
        data = request.model_dump(exclude_unset=True)
        if "email" in data and self.user_repo.find_by_email(data["email"], exclude_id=user.id):
            raise ValueError("Email already in use")

        if "phone" in data and data["phone"] and self.user_repo.find_by_phone(
            data["phone"], exclude_id=user.id
        ):
            raise ValueError("Phone already in use")

        for field, value in data.items():
            setattr(user, field, value)

        self.user_repo.commit()
        self.user_repo.refresh(user, attribute_names=["role"])
        return user

    def change_password(self, user: User, request: ChangePasswordRequest) -> None:
        if not verify_password(request.current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")

        user.hashed_password = get_password_hash(request.new_password)
        user.password_changed_at = datetime.now(UTC).replace(tzinfo=None)
        user.must_change_password = False
        self.user_repo.commit()

    def admin_update(self, user: User, request: AdminUpdateUserRequest, admin: User) -> User:
        data = request.model_dump(exclude_unset=True)
        if "role_id" in data and data["role_id"] is not None:
            role = self.role_repo.get_active_by_id(data["role_id"])
            if role is None:
                raise ValueError("Role not found or inactive")
            data["role_id"] = role.id

        for field, value in data.items():
            setattr(user, field, value)
        user.updated_by_id = admin.id
        self.user_repo.commit()
        self.user_repo.refresh(user, attribute_names=["role"])
        return user

    def soft_delete(self, user: User, actor: User | None = None) -> None:
        user.deleted_at = datetime.now(UTC).replace(tzinfo=None)
        user.is_active = False
        if actor:
            user.updated_by_id = actor.id
        self.user_repo.commit()

    def record_login_success(self, user: User, client_ip: str | None = None) -> None:
        user.last_login_at = datetime.now(UTC).replace(tzinfo=None)
        user.last_login_ip = client_ip
        user.failed_login_attempts = 0
        user.locked_until = None
        self.user_repo.commit()

    def authenticate(self, identifier: str, password: str) -> User:
        user = self.get_by_username_or_email(identifier)
        if user is None or not verify_password(password, user.hashed_password):
            self.record_login_failure(user)
            raise ValueError("invalid_credentials")
        if user.is_locked:
            raise ValueError("account_locked")
        if not user.is_active:
            raise ValueError("inactive_user")
        return user

    def record_login_failure(self, user: User | None) -> None:
        if user is None:
            return
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
            user.locked_until = datetime.now(UTC).replace(tzinfo=None) + timedelta(
                minutes=LOCK_DURATION_MINUTES
            )
            logger.warning("User locked: id=%s until %s", user.id, user.locked_until)
        self.user_repo.commit()
