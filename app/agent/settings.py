"""Backend switches for the support agent.

`agent.env` holds the switches Cody may change on screen during a demo.
`.env` holds API keys and is never opened in front of a client. Both are
gitignored and read again on every chat message, so an edit applies to the
next reply without a restart.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

from app.inputs import valid_email

ROOT = Path(__file__).resolve().parent.parent.parent
AGENT_ENV_PATH = ROOT / "agent.env"
SECRETS_PATH = ROOT / ".env"

DEFAULT_MODELS = {
    "anthropic": "claude-opus-5-5",
    "ollama": "lumen-gemma",
    "openai": "",
    "gemini": "",
}
EFFORTS = {"low", "medium", "high", "xhigh", "max"}
DEFAULT_SUPPORT_EMAIL = "help@lumenbeauty.example"

# Hard ceilings the settings cannot exceed. Request bodies are capped at 64 KB
# and the transcript store was built around 100 messages per chat.
MESSAGE_CHARS_CEILING = 2000
MESSAGES_PER_CHAT_CEILING = 100


@dataclass(frozen=True)
class AgentSettings:
    provider: str
    model: str
    effort: str
    show_details: bool
    support_email: str
    live_chat_url: str
    ollama_url: str
    max_message_chars: int
    max_messages_per_chat: int
    rate_per_minute: int
    rate_per_hour_per_ip: int
    max_tokens_per_reply: int
    off_topic_limit: int
    daily_budget_usd: float
    visitor_daily_budget_usd: float
    trust_proxy_headers: bool


def _values(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return {key: value for key, value in dotenv_values(path).items() if value is not None}


def _flag(value: str | None, default: bool) -> bool:
    if value is None or not value.strip():
        return default
    return value.strip().lower() not in {"false", "0", "no", "off"}


def _int(value: str | None, default: int, low: int, high: int) -> int:
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        return default
    return min(max(number, low), high)


def _money(value: str | None, default: float) -> float:
    """A dollar amount; 0 turns that cap off."""
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return default
    return number if number >= 0 else default


def _web_url(value: str) -> str:
    """Only http(s) links may reach the page, never javascript: or data:."""
    value = value.strip()
    return value if value.startswith(("https://", "http://")) else ""


def load_settings() -> AgentSettings:
    values = _values(AGENT_ENV_PATH)
    provider = values.get("AGENT_PROVIDER", "anthropic").strip().lower()
    effort = values.get("AGENT_EFFORT", "low").strip().lower()
    email = values.get("SUPPORT_EMAIL", "").strip()
    return AgentSettings(
        provider=provider,
        model=values.get("AGENT_MODEL", "").strip() or DEFAULT_MODELS.get(provider, ""),
        effort=effort if effort in EFFORTS else "low",
        show_details=_flag(values.get("AGENT_SHOW_DETAILS"), True),
        support_email=email if valid_email(email) else DEFAULT_SUPPORT_EMAIL,
        live_chat_url=_web_url(values.get("LIVE_CHAT_URL", "")),
        ollama_url=_web_url(values.get("OLLAMA_URL", "")) or "http://127.0.0.1:11434",
        max_message_chars=_int(values.get("AGENT_MAX_MESSAGE_CHARS"), 1000, 50, MESSAGE_CHARS_CEILING),
        max_messages_per_chat=_int(values.get("AGENT_MAX_MESSAGES_PER_CHAT"), 30, 1, MESSAGES_PER_CHAT_CEILING),
        rate_per_minute=_int(values.get("AGENT_RATE_PER_MINUTE"), 6, 1, 600),
        rate_per_hour_per_ip=_int(values.get("AGENT_RATE_PER_HOUR_PER_IP"), 60, 1, 100_000),
        max_tokens_per_reply=_int(values.get("AGENT_MAX_TOKENS_PER_REPLY"), 60_000, 1_000, 1_000_000),
        off_topic_limit=_int(values.get("AGENT_OFF_TOPIC_LIMIT"), 3, 1, 100),
        daily_budget_usd=_money(values.get("AGENT_DAILY_BUDGET_USD"), 5.0),
        visitor_daily_budget_usd=_money(values.get("AGENT_VISITOR_DAILY_BUDGET_USD"), 1.0),
        trust_proxy_headers=_flag(values.get("TRUST_PROXY_HEADERS"), False),
    )


def secret(name: str) -> str | None:
    """An API key from `.env`, falling back to the process environment."""
    value = _values(SECRETS_PATH).get(name) or os.environ.get(name)
    return value.strip() if value and value.strip() else None
