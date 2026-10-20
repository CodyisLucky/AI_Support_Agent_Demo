"""Three-digit error codes and the log line written for each one."""

from datetime import datetime, timezone

from app.storage import append_error

# A signed-in session expires after this long without another page load.
SESSION_IDLE_SECONDS = 30 * 60

# Shopper outcome: the processor answered and refused this card.
DECLINED_CARD = "4000000000000002"

CODES = {
    "101": "That username and password do not match.",
    "102": "Your session expired. Sign in again.",
    "103": "That username is already registered.",
    "201": "That card was declined. Try a different card.",
    "202": "That item is out of stock.",
    "203": "Your cart is empty.",
    "301": "That order could not be found.",
    "500": "Something went wrong on our side. Nothing was changed. Try again.",
    "501": "The payment processor is unavailable. Nothing was charged. Try again in a few minutes.",
    "502": "The network is unavailable. Nothing was changed. Try again in a few minutes.",
    "503": "The account could not be created. Nothing was saved. Try again.",
    "504": "The order could not be saved. Nothing was charged. Your cart is still here.",
    "505": "The order was placed, but the card was not saved to the account.",
    "506": "Your account records could not be loaded. Try again in a few minutes.",
    "507": "The payment processor timed out. Nothing was charged. Try the order once more.",
}


def message(code: str) -> str:
    return CODES[code]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def session_is_stale(signed_in_at: str, now: datetime | None = None) -> bool:
    try:
        started = datetime.fromisoformat(signed_in_at)
    except ValueError:
        return True
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    current = now or datetime.now(timezone.utc)
    return (current - started).total_seconds() >= SESSION_IDLE_SECONDS


def card_digits(number: str) -> str:
    return "".join(character for character in number if character.isdigit())


def log_error(
    user_id: str | None,
    code: str,
    detail: str = "",
    session_id: str | None = None,
) -> None:
    try:
        append_error(
            {
                "time": utc_now(),
                "session_id": session_id,
                "user_id": user_id,
                "code": code,
                "detail": detail,
            }
        )
    except Exception:
        return
