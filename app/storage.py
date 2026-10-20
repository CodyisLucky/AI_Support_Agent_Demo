import json
import secrets
from pathlib import Path
from threading import Lock

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
USERS_PATH = DATA_DIR / "users.json"
ORDERS_PATH = DATA_DIR / "orders.json"
SECRET_PATH = DATA_DIR / "session_secret"

_lock = Lock()

DEMO_USERNAME = "demo"
DEMO_DISPLAY_NAME = "Demo Shopper"
DEMO_PASSWORD = "demo-shopper"


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def session_secret() -> str:
    ensure_data_dir()
    if SECRET_PATH.exists():
        secret = SECRET_PATH.read_text(encoding="utf-8").strip()
        if secret:
            return secret
    secret = secrets.token_urlsafe(32)
    SECRET_PATH.write_text(secret, encoding="utf-8")
    return secret


def _read_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    ensure_data_dir()
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def load_users() -> list[dict]:
    with _lock:
        payload = _read_json(USERS_PATH, {"users": []})
        return list(payload.get("users", []))


def save_users(users: list[dict]) -> None:
    with _lock:
        _write_json(USERS_PATH, {"users": users})


def load_orders() -> list[dict]:
    with _lock:
        payload = _read_json(ORDERS_PATH, {"orders": []})
        return list(payload.get("orders", []))


def get_order(order_id: str) -> dict | None:
    for order in load_orders():
        if order.get("id") == order_id:
            return order
    return None


def orders_for_user(user_id: str) -> list[dict]:
    orders = [order for order in load_orders() if order.get("user_id") == user_id]
    return list(reversed(orders))


def append_order(order: dict) -> None:
    with _lock:
        payload = _read_json(ORDERS_PATH, {"orders": []})
        orders = list(payload.get("orders", []))
        orders.append(order)
        _write_json(ORDERS_PATH, {"orders": orders})
