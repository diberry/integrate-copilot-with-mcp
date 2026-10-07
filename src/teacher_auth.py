import hashlib
import hmac
import json
import secrets
from pathlib import Path


ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600_000
SALT_BYTES = 16


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password cannot be empty")

    salt = secrets.token_hex(SALT_BYTES)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        bytes.fromhex(salt),
        ITERATIONS,
    ).hex()
    return f"{ALGORITHM}${ITERATIONS}${salt}${password_hash}"


def verify_password(password: str, encoded_password: str) -> bool:
    try:
        algorithm, iterations_text, salt, expected_hash = encoded_password.split("$")
        iterations = int(iterations_text)
        if algorithm != ALGORITHM or iterations <= 0:
            return False
        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            bytes.fromhex(salt),
            iterations,
        ).hex()
    except (TypeError, ValueError):
        return False

    return hmac.compare_digest(actual_hash, expected_hash)


def load_teacher_credentials(path: Path) -> dict[str, str]:
    try:
        data = json.loads(path.read_text())
    except FileNotFoundError as error:
        raise RuntimeError(f"Teacher credential file not found: {path}") from error
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Teacher credential file is not valid JSON: {path}") from error

    if not isinstance(data, dict):
        raise RuntimeError("Teacher credential file must contain a JSON object")

    teachers = data.get("teachers")
    if not isinstance(teachers, list):
        raise RuntimeError("Teacher credential file must contain a teachers list")

    credentials: dict[str, str] = {}
    for teacher in teachers:
        if not isinstance(teacher, dict):
            raise RuntimeError("Each teacher credential must be an object")
        username = teacher.get("username")
        password_hash = teacher.get("password_hash")
        if not isinstance(username, str) or not username:
            raise RuntimeError("Each teacher must have a non-empty username")
        if not isinstance(password_hash, str) or not password_hash:
            raise RuntimeError(f"Teacher {username!r} must have a password hash")
        if username in credentials:
            raise RuntimeError(f"Duplicate teacher username: {username}")
        credentials[username] = password_hash

    return credentials
