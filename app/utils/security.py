import re
from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password: str) -> str:
    """
    Hash a plain text password.
    """
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a plain text password against a stored hash.
    """
    return check_password_hash(password, password_hash)


def is_strong_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength.

    Rules:
    - at least 8 characters
    - at least one number OR one special character
    """

    if len(password) < 8:
        return False, "Password must be at least 8 characters long."

    has_number = re.search(r"\d", password)
    has_special = re.search(r"[^\w\s]", password)

    if not has_number and not has_special:
        return False, "Password must contain at least one number or special character."

    return True, "Password is valid."