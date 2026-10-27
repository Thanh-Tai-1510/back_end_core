from sqlalchemy import String
from sqlalchemy.types import TypeDecorator

from src.base.models.enums import AuthProvider, Gender, UserRole


class UserRoleType(TypeDecorator):
    impl = String(20)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, UserRole):
            return value.value
        return UserRole.from_value(str(value)).value

    def process_result_value(self, value, dialect):
        return UserRole.from_value(value)


class GenderType(TypeDecorator):
    impl = String(20)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, Gender):
            return value.value
        return Gender.from_value(str(value)).value

    def process_result_value(self, value, dialect):
        return Gender.from_value(value)


class AuthProviderType(TypeDecorator):
    impl = String(20)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, AuthProvider):
            return value.value
        return AuthProvider.from_value(str(value)).value

    def process_result_value(self, value, dialect):
        return AuthProvider.from_value(value)
