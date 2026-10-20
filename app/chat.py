"""Shopper chat for one browser visit. The reply is a stub until step 6."""

from app.storage import append_chat_turn, chat_for_session

MAX_MESSAGE_LENGTH = 2000
SHOPPER_TURN_LIMIT = 100
STUB_REPLY = "I have your message. The support agent is not connected yet."


def clean_message(raw: str) -> str:
    return " ".join(raw.split())


def stub_reply(_text: str) -> str:
    return STUB_REPLY


def visible_messages(session_id: str) -> list[dict]:
    chat = chat_for_session(session_id)
    if not chat:
        return []
    visible = []
    for message in chat.get("messages", []):
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        text = message.get("text")
        if role in ("shopper", "agent") and isinstance(text, str) and text:
            visible.append({"role": role, "text": text})
    return visible


def record_turn(session_id: str, user_id: str | None, text: str) -> list[dict]:
    saved = append_chat_turn(
        session_id,
        user_id,
        text,
        stub_reply(text),
        limit=SHOPPER_TURN_LIMIT,
    )
    return [{"role": message["role"], "text": message["text"]} for message in saved]
