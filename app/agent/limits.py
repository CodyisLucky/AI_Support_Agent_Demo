"""Safeguards that keep the chat a shopping helper, not a free AI.

Rate limits stop floods: messages per minute in one chat and per hour from
one network. They live in memory and reset on restart. Daily caps stop
spend: a total for all visitors and one per visitor, read from
`data/usage.json`, which holds today only.

A visitor is their account when signed in, otherwise their IP address. The
raw IP is never stored: it is hashed with a key derived from the shop's
secret and today's date, so hashes change every day and cannot link visits.
"""

import hashlib
import hmac
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock

from app.storage import session_secret

MINUTE = 60
HOUR = 60 * 60


@dataclass(frozen=True)
class Visitor:
    usage_key: str  # "account:<id>" or "ip:<daily hash>"
    network_key: str  # "ip:<daily hash>", for the per-network rate limit


def today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _daily_key(day: str) -> bytes:
    return hmac.new(session_secret().encode(), f"visitor-key:{day}".encode(), hashlib.sha256).digest()


def ip_hash(ip: str, day: str | None = None) -> str:
    return hmac.new(_daily_key(day or today()), ip.encode(), hashlib.sha256).hexdigest()[:20]


def client_ip(direct: str | None, forwarded_for: str | None, trust_proxy_headers: bool) -> str:
    """The visitor's address. X-Forwarded-For can be forged by anyone, so it
    is used only when the shop is told it sits behind a proxy that sets it."""
    if trust_proxy_headers and forwarded_for:
        first = forwarded_for.split(",")[0].strip()
        if first:
            return first
    return direct or "unknown"


def visitor_for(user_id: str | None, ip: str) -> Visitor:
    network = f"ip:{ip_hash(ip)}"
    return Visitor(usage_key=f"account:{user_id}" if user_id else network, network_key=network)


def reset_note(now: datetime | None = None) -> str:
    """When the daily caps reset, said plainly."""
    current = now or datetime.now(timezone.utc)
    midnight = datetime.combine(current.date() + timedelta(days=1), datetime.min.time(), timezone.utc)
    hours = max(1, round((midnight - current).total_seconds() / HOUR))
    return f"at midnight UTC (in about {hours} hour{'s' if hours != 1 else ''})"


class RateLimiter:
    """Sliding-window counters kept in memory."""

    def __init__(self):
        self._hits: dict[str, deque] = {}
        self._warned: dict[str, float] = {}
        self._lock = Lock()

    def allow(self, key: str, limit: int, window: int, now: float | None = None) -> tuple[bool, bool]:
        """Record a hit if allowed. Returns (allowed, first_refusal_in_window),
        so a flood writes one error-log line per window, not one per message."""
        current = time.monotonic() if now is None else now
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and hits[0] <= current - window:
                hits.popleft()
            if len(hits) < limit:
                hits.append(current)
                return True, False
            first = self._warned.get(key, -1.0) <= current - window
            if first:
                self._warned[key] = current
            if len(self._hits) > 10_000:
                self._prune(current)
            return False, first

    def _prune(self, current: float) -> None:
        for key in [key for key, hits in self._hits.items() if not hits or hits[-1] <= current - HOUR]:
            del self._hits[key]
            self._warned.pop(key, None)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()
            self._warned.clear()


RATE_LIMITER = RateLimiter()
