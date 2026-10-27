SENSITIVE_KEY_PARTS = ("secret", "password", "token", "private", "credential")


def is_sensitive_key(key: str) -> bool:
    lower = key.lower()
    return any(part in lower for part in SENSITIVE_KEY_PARTS)


def mask_config_value(key: str, value: str | None, *, reveal: bool = False) -> str | None:
    if reveal or value is None or not is_sensitive_key(key):
        return value
    return "********"
