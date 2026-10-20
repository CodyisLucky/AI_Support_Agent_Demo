import hashlib
import hmac
import re
import secrets
import uuid
from datetime import datetime, timezone

from app.storage import (
    DEMO_DISPLAY_NAME,
    DEMO_PASSWORD,
    DEMO_USERNAME,
    load_users,
    save_users,
)

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,32}$")
USERNAME_TAKEN = "That username is already registered."
MIN_PASSWORD_LENGTH = 8
HASH_ITERATIONS = 200_000


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        HASH_ITERATIONS,
    )
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt, _, _digest = stored.partition("$")
    if not salt or not _digest:
        return False
    return hmac.compare_digest(hash_password(password, salt), stored)


def public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "username": user["username"],
        "display_name": user["display_name"],
        "created_at": user["created_at"],
        "saved_card": user.get("saved_card"),
    }


def find_user(username: str) -> dict | None:
    key = username.strip().lower()
    for user in load_users():
        if user["username"].lower() == key:
            return user
    return None


def find_user_by_id(user_id: str) -> dict | None:
    for user in load_users():
        if user["id"] == user_id:
            return user
    return None


def validate_new_account(username: str, display_name: str, password: str, confirm: str) -> str | None:
    username = username.strip()
    display_name = display_name.strip()
    if not USERNAME_PATTERN.fullmatch(username):
        return "Usernames are 3–32 characters and use letters, numbers, or underscores."
    if not display_name or len(display_name) > 60:
        return "Enter a display name up to 60 characters."
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Passwords need at least {MIN_PASSWORD_LENGTH} characters."
    if password != confirm:
        return "Those passwords do not match."
    if find_user(username):
        return USERNAME_TAKEN
    return None


def save_card(user_id: str, card: dict) -> None:
    users = load_users()
    for user in users:
        if user["id"] == user_id:
            user["saved_card"] = card
            break
    save_users(users)


def create_user(username: str, display_name: str, password: str) -> dict:
    user = {
        "id": str(uuid.uuid4()),
        "username": username.strip(),
        "display_name": display_name.strip(),
        "password_hash": hash_password(password),
        "created_at": _now(),
    }
    users = load_users()
    users.append(user)
    save_users(users)
    return user


def authenticate(username: str, password: str) -> dict | None:
    user = find_user(username)
    if not user or not verify_password(password, user["password_hash"]):
        return None
    return user


def ensure_demo_user() -> None:
    if find_user(DEMO_USERNAME):
        return
    create_user(DEMO_USERNAME, DEMO_DISPLAY_NAME, DEMO_PASSWORD)
