import json
import os
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
USERS_PATH = DATA_DIR / "users.json"
ORDERS_PATH = DATA_DIR / "orders.json"
CHATS_PATH = DATA_DIR / "chats.json"
ERRORS_PATH = DATA_DIR / "errors.jsonl"
SECRET_PATH = DATA_DIR / "session_secret"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
USAGE_PATH = DATA_DIR / "usage.json"

# Conversation ids are typed by shoppers into an email, so they are short and
# skip characters that look alike (0/O, 1/I/L).
CONVERSATION_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"

_lock = Lock()


class StorageError(Exception):
    def __init__(self, operation: str):
        self.operation = operation
        super().__init__(operation)


class ChatFull(Exception):
    """This visit's transcript has reached the shopper-message limit."""

DEMO_USERNAME = "demo"
DEMO_DISPLAY_NAME = "Demo Shopper"
DEMO_PASSWORD = "demo-shopper"


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def session_secret() -> str:
    ensure_data_dir()
    if SECRET_PATH.exists():
        SECRET_PATH.chmod(0o600)
        secret = SECRET_PATH.read_text(encoding="utf-8").strip()
        if secret:
            return secret
    secret = secrets.token_urlsafe(32)
    descriptor = os.open(SECRET_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(secret)
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
    try:
        with _lock:
            payload = _read_json(USERS_PATH, {"users": []})
            return list(payload.get("users", []))
    except (OSError, json.JSONDecodeError) as exc:
        raise StorageError("read users") from exc


def save_users(users: list[dict]) -> None:
    try:
        with _lock:
            _write_json(USERS_PATH, {"users": users})
    except OSError as exc:
        raise StorageError("write users") from exc


def load_orders() -> list[dict]:
    try:
        with _lock:
            payload = _read_json(ORDERS_PATH, {"orders": []})
            return list(payload.get("orders", []))
    except (OSError, json.JSONDecodeError) as exc:
        raise StorageError("read orders") from exc


def get_order(order_id: str) -> dict | None:
    for order in load_orders():
        if order.get("id") == order_id:
            return order
    return None


def orders_for_user(user_id: str) -> list[dict]:
    orders = [order for order in load_orders() if order.get("user_id") == user_id]
    return list(reversed(orders))


def append_order(order: dict) -> None:
    try:
        with _lock:
            payload = _read_json(ORDERS_PATH, {"orders": []})
            orders = list(payload.get("orders", []))
            orders.append(order)
            _write_json(ORDERS_PATH, {"orders": orders})
    except (OSError, json.JSONDecodeError) as exc:
        raise StorageError("write orders") from exc


def append_error(entry: dict) -> None:
    line = json.dumps(entry, separators=(",", ":")) + "\n"
    with _lock:
        ensure_data_dir()
        with ERRORS_PATH.open("a", encoding="utf-8") as handle:
            handle.write(line)


def _read_errors() -> list[dict]:
    if not ERRORS_PATH.exists():
        return []
    with _lock:
        lines = ERRORS_PATH.read_text(encoding="utf-8").splitlines()
    entries: list[dict] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(entry, dict):
            entries.append(entry)
    return entries


def _recent(entries: list[dict], limit: int) -> list[dict]:
    if limit < 1:
        return []
    return list(reversed(entries[-limit:]))


def errors_for_user(user_id: str, limit: int = 20) -> list[dict]:
    matched = [entry for entry in _read_errors() if entry.get("user_id") == user_id]
    return _recent(matched, limit)


def errors_for_session(session_id: str, limit: int = 50) -> list[dict]:
    matched = [entry for entry in _read_errors() if entry.get("session_id") == session_id]
    return _recent(matched, limit)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_chats() -> list[dict]:
    payload = _read_json(CHATS_PATH, {"chats": []})
    return [chat for chat in payload.get("chats", []) if isinstance(chat, dict)]


def all_chats() -> list[dict]:
    try:
        with _lock:
            return _load_chats()
    except (OSError, json.JSONDecodeError) as exc:
        raise StorageError("read chats") from exc


def chat_for_session(session_id: str) -> dict | None:
    for chat in all_chats():
        if chat.get("session_id") == session_id:
            return chat
    return None


def _new_conversation_id(chats: list[dict]) -> str:
    taken = {chat.get("conversation_id") for chat in chats}
    while True:
        candidate = "LB-" + "".join(secrets.choice(CONVERSATION_ALPHABET) for _ in range(6))
        if candidate not in taken:
            return candidate


def _new_chat(session_id: str, user_id: str | None, chats: list[dict], now: str) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "conversation_id": _new_conversation_id(chats),
        "session_id": session_id,
        "user_id": user_id,
        "created_at": now,
        "updated_at": now,
        "messages": [],
    }


def open_chat(session_id: str, user_id: str | None) -> dict:
    """Return this visit's chat, creating it (with a conversation id) if needed.

    A chat saved before conversation ids existed is given one here.
    """
    now = _utc_now()
    try:
        with _lock:
            chats = _load_chats()
            chat = next((item for item in chats if item.get("session_id") == session_id), None)
            if chat is None:
                chat = _new_chat(session_id, user_id, chats, now)
                chats.append(chat)
            elif not chat.get("conversation_id"):
                chat["conversation_id"] = _new_conversation_id(chats)
            else:
                return chat
            _write_json(CHATS_PATH, {"chats": chats})
            return chat
    except (OSError, json.JSONDecodeError) as exc:
        raise StorageError("write chats") from exc


def append_chat_turn(
    session_id: str,
    user_id: str | None,
    shopper_text: str,
    agent_text: str,
    limit: int = 100,
    agent_meta: dict | None = None,
    handoff: dict | None = None,
) -> list[dict]:
    """Save one shopper message and the reply that follows it.

    `agent_meta` (provider, model, timing, lookups) is kept on the reply.
    `handoff` marks the chat as passed to the business; it is the local
    support ticket, and the first one saved wins.

    Returns those two messages. Raises ChatFull when this session already
    holds `limit` shopper messages, and StorageError when the file cannot
    be written.
    """
    now = _utc_now()
    shopper = {"role": "shopper", "text": shopper_text, "time": now, "user_id": user_id}
    agent = {"role": "agent", "text": agent_text, "time": now}
    if agent_meta:
        agent["meta"] = agent_meta
    try:
        with _lock:
            chats = _load_chats()
            chat = next((item for item in chats if item.get("session_id") == session_id), None)
            if chat is None:
                chat = _new_chat(session_id, user_id, chats, now)
                chats.append(chat)
            messages = [item for item in chat.get("messages", []) if isinstance(item, dict)]
            shopper_count = sum(1 for item in messages if item.get("role") == "shopper")
            if shopper_count >= limit:
                raise ChatFull()
            messages.extend([shopper, agent])
            chat["messages"] = messages
            chat["user_id"] = user_id
            chat["updated_at"] = now
            if handoff and not chat.get("handoff"):
                chat["handoff"] = {**handoff, "time": now}
            _write_json(CHATS_PATH, {"chats": chats})
    except ChatFull:
        raise
    except (OSError, json.JSONDecodeError) as exc:
        raise StorageError("write chats") from exc
    return [shopper, agent]


def write_text_file(path: Path, text: str) -> None:
    """Replace a file in one step so a reader never sees half of it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _today_usage(day: str) -> dict:
    payload = _read_json(USAGE_PATH, {})
    if payload.get("date") != day:
        return {"date": day, "total_usd": 0.0, "visitors": {}}
    return payload


def usage_for_day(day: str) -> dict:
    """Today's estimated AI spend: the total and per visitor key.

    Only one day is ever kept. Visitor keys for guests are a hash of the IP
    address under a key that changes daily, so nothing here links visits
    across days.
    """
    try:
        with _lock:
            return _today_usage(day)
    except (OSError, json.JSONDecodeError) as exc:
        raise StorageError("read usage") from exc


def add_usage(day: str, visitor_key: str, usd: float) -> None:
    """Add one reply's estimated cost. The first write of a new day drops
    the previous day's entries."""
    try:
        with _lock:
            usage = _today_usage(day)
            usage["total_usd"] = round(usage.get("total_usd", 0.0) + usd, 6)
            visitors = usage.setdefault("visitors", {})
            visitors[visitor_key] = round(visitors.get(visitor_key, 0.0) + usd, 6)
            _write_json(USAGE_PATH, usage)
    except (OSError, json.JSONDecodeError) as exc:
        raise StorageError("write usage") from exc
