"""Shopper chat for one browser visit, answered by the support agent."""

import re

from app.agent.context import ShopperContext
from app.agent.handoff import REASON_LABELS, contact, daily_cap_text
from app.agent.limits import HOUR, MINUTE, RATE_LIMITER, Visitor, reset_note, today
from app.agent.providers import label
from app.agent.records import write_records
from app.agent.service import AgentAnswer, answer
from app.agent.settings import AgentSettings, load_settings
from app.errors import log_error
from app.inputs import clean_text
from app.storage import (
    ChatFull,
    StorageError,
    add_usage,
    append_chat_turn,
    chat_for_session,
    open_chat,
    usage_for_day,
)

CAP_LABELS = {
    "daily_total": "daily cap for all visitors",
    "visitor_daily": "daily cap for this visitor",
}

# Earlier messages sent to the model with each new one.
HISTORY_MESSAGES = 20

CARD_REDACTED = "[card number removed]"
# 12 to 19 digits, optionally split by single spaces or dashes: the same
# shape checkout accepts as a card number.
_CARD_LIKE = re.compile(r"(?<!\d)\d(?:[ -]?\d){11,18}(?!\d)")


class Limited(Exception):
    """A rate limit refused the message before anything was saved.

    `first` is true for the first refusal in its window, so a flood logs one
    line rather than one per message.
    """

    def __init__(self, message: str, detail: str, first: bool):
        self.message = message
        self.detail = detail
        self.first = first
        super().__init__(detail)


def redact(text: str) -> str:
    """Remove anything shaped like a card number. The error log never stores
    one, and neither do transcripts or the AI provider."""
    return _CARD_LIKE.sub(CARD_REDACTED, text)


def clean_message(raw: str) -> str:
    return redact(clean_text(raw))


def details_line(meta: dict | None) -> str:
    """The muted line under a reply: who answered, how fast, at what cost,
    and what it looked up."""
    if not meta or meta.get("kind") == "paused":
        return ""
    if meta.get("kind") == "limit":
        return f"Shop safeguard · {CAP_LABELS.get(meta.get('limit'), meta.get('limit', ''))} reached"
    parts = [label(meta.get("provider", ""))]
    if meta.get("model"):
        parts.append(meta["model"])
    if meta.get("latency_ms") is not None:
        parts.append(f"{meta['latency_ms'] / 1000:.1f} s")
    if meta.get("input_tokens") or meta.get("output_tokens"):
        parts.append(f"{meta.get('input_tokens', 0):,} in / {meta.get('output_tokens', 0):,} out")
    if meta.get("est_cost_usd") is not None:
        parts.append(f"~${meta['est_cost_usd']:.4f}")
    if meta.get("kind") == "off_topic":
        parts.append(f"off topic: {meta.get('topic', '')}")
    if meta.get("error"):
        parts.append(f"stopped: {REASON_LABELS.get(meta.get('error'), meta.get('error', ''))}")
    lookups = meta.get("lookups") or []
    if lookups:
        parts.append("looked up: " + ", ".join(lookups))
    elif meta.get("kind") == "answer":
        parts.append("no lookup")
    return " · ".join(parts)


def _messages(chat: dict | None) -> list[dict]:
    if not chat:
        return []
    return [
        message
        for message in chat.get("messages", [])
        if isinstance(message, dict)
        and message.get("role") in ("shopper", "agent")
        and isinstance(message.get("text"), str)
        and message["text"]
    ]


def message_view(message: dict, show_details: bool) -> dict:
    text = message["text"]
    view = {
        "role": message["role"],
        "text": text,
        "paragraphs": [paragraph for paragraph in text.split("\n\n") if paragraph.strip()],
    }
    if show_details and message["role"] == "agent":
        details = details_line(message.get("meta"))
        if details:
            view["details"] = details
    return view


def _handoff_view(chat: dict | None, settings: AgentSettings) -> dict | None:
    handoff = (chat or {}).get("handoff")
    if not handoff or not chat.get("conversation_id"):
        return None
    return contact(settings, chat["conversation_id"], handoff.get("summary", ""))


def chat_view(session_id: str) -> dict:
    """Everything the chat panel shows for this visit."""
    settings = load_settings()
    chat = chat_for_session(session_id)
    return {
        "messages": [message_view(message, settings.show_details) for message in _messages(chat)],
        "conversation_id": (chat or {}).get("conversation_id"),
        "handoff": _handoff_view(chat, settings),
    }


def _history(messages: list[dict]) -> list[dict]:
    recent = messages[-HISTORY_MESSAGES:]
    while recent and recent[0]["role"] != "shopper":
        recent = recent[1:]
    return [
        {"role": "user" if message["role"] == "shopper" else "assistant", "text": message["text"]}
        for message in recent
    ]


def _check_rate(session_id: str, visitor: Visitor, settings: AgentSettings) -> None:
    allowed, first = RATE_LIMITER.allow(f"chat:{session_id}", settings.rate_per_minute, MINUTE)
    if not allowed:
        raise Limited(
            "You're sending messages faster than our assistant can answer. Wait a minute, then try again.",
            "rate limit: messages per minute in one chat",
            first,
        )
    allowed, first = RATE_LIMITER.allow(visitor.network_key, settings.rate_per_hour_per_ip, HOUR)
    if not allowed:
        raise Limited(
            "Too many messages have come from your network in the last hour, so the assistant is pausing. "
            f"Try again later, or email our team at {settings.support_email}.",
            "rate limit: messages per hour from one network",
            first,
        )


def _cap_reached(day: str, visitor: Visitor, settings: AgentSettings) -> str | None:
    """Which daily cap, if any, is already used up. A cap of 0 is off.
    Caps are checked before a reply, so the reply that crosses one finishes."""
    if not settings.daily_budget_usd and not settings.visitor_daily_budget_usd:
        return None
    usage = usage_for_day(day)
    if settings.daily_budget_usd and usage.get("total_usd", 0) >= settings.daily_budget_usd:
        return "daily_total"
    spent = usage.get("visitors", {}).get(visitor.usage_key, 0)
    if settings.visitor_daily_budget_usd and spent >= settings.visitor_daily_budget_usd:
        return "visitor_daily"
    return None


def _off_topic_count(messages: list[dict]) -> int:
    return sum(1 for message in messages if (message.get("meta") or {}).get("kind") == "off_topic")


def record_turn(
    session_id: str,
    user_id: str | None,
    username: str | None,
    order_ids: list[str],
    text: str,
    visitor: Visitor,
) -> dict:
    """Answer one shopper message and save both sides.

    Raises Limited (nothing saved) when a rate limit refuses the message,
    ChatFull before calling the model when the chat is at its message limit,
    and StorageError when the chat cannot be read or saved.
    """
    settings = load_settings()
    _check_rate(session_id, visitor, settings)
    chat = open_chat(session_id, user_id)
    earlier = _messages(chat)
    if sum(1 for message in earlier if message["role"] == "shopper") >= settings.max_messages_per_chat:
        raise ChatFull()
    context = ShopperContext(
        session_id=session_id,
        user_id=user_id,
        username=username,
        order_ids=tuple(order_ids),
        conversation_id=chat["conversation_id"],
    )
    day = today()
    handed_off = bool(chat.get("handoff"))
    cap = None if handed_off else _cap_reached(day, visitor, settings)
    if cap:
        log_error(user_id, "509", detail=f"{CAP_LABELS[cap]} reached", session_id=session_id)
        result = AgentAnswer(
            daily_cap_text(settings, context.conversation_id, reset_note()),
            {"kind": "limit", "limit": cap},
        )
    else:
        result = answer(
            context,
            _history(earlier),
            text,
            settings,
            handed_off=handed_off,
            off_topic_count=_off_topic_count(earlier),
        )
    saved = append_chat_turn(
        session_id,
        user_id,
        text,
        result.text,
        limit=settings.max_messages_per_chat,
        agent_meta=result.meta,
        handoff=result.handoff,
    )
    cost = result.meta.get("est_cost_usd") or 0
    if cost:
        try:
            add_usage(day, visitor.usage_key, cost)
        except StorageError:
            log_error(user_id, "500", detail="write usage", session_id=session_id)
    try:
        write_records(session_id)
    except (OSError, StorageError):
        log_error(user_id, "500", detail="write transcripts", session_id=session_id)
    handoff = chat.get("handoff") or result.handoff
    return {
        "messages": [message_view(message, settings.show_details) for message in saved],
        "conversation_id": context.conversation_id,
        "handoff": _handoff_view({**chat, "handoff": handoff}, settings),
    }
