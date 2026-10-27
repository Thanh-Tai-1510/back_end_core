import enum


class UserRole(str, enum.Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SYSTEM = "system"

    @classmethod
    def from_value(cls, value: str | None) -> "UserRole":
        if not value:
            return cls.USER
        normalized = value.strip().lower()
        for role in cls:
            if role.value == normalized or role.name.lower() == normalized:
                return role
        return cls.USER


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNSPECIFIED = "unspecified"

    @classmethod
    def from_value(cls, value: str | None) -> "Gender":
        if not value:
            return cls.UNSPECIFIED
        normalized = value.strip().lower()
        for item in cls:
            if item.value == normalized or item.name.lower() == normalized:
                return item
        return cls.UNSPECIFIED


class AuthProvider(str, enum.Enum):
    LOCAL = "local"
    GOOGLE = "google"
    FACEBOOK = "facebook"
    GITHUB = "github"

    @classmethod
    def from_value(cls, value: str | None) -> "AuthProvider":
        if not value:
            return cls.LOCAL
        normalized = value.strip().lower()
        for item in cls:
            if item.value == normalized or item.name.lower() == normalized:
                return item
        return cls.LOCAL


class PermissionEffect(str, enum.Enum):
    GRANT = "grant"
    DENY = "deny"

    @classmethod
    def from_value(cls, value: str | None) -> "PermissionEffect":
        if not value:
            return cls.GRANT
        normalized = value.strip().lower()
        for item in cls:
            if item.value == normalized or item.name.lower() == normalized:
                return item
        return cls.GRANT
