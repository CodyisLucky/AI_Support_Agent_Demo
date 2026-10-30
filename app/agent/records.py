"""Readable conversation records for the business.

After every message the shop rewrites `data/transcripts/<conversation id>.md`
and `data/transcripts/index.md`. They are plain local files: nothing is sent
anywhere and there is no web page over them. Shopper text is quoted so it
cannot pose as a heading or a note from the shop.
"""

from app.auth import find_user_by_id
from app.errors import CODES
from app.storage import TRANSCRIPTS_DIR, StorageError, all_chats, errors_for_session, write_text_file

from .handoff import REASON_LABELS, error_code, is_failure
from .providers import label

INDEX_PATH = TRANSCRIPTS_DIR / "index.md"


def _safe(text: object) -> str:
    """One line of shopper or model text, safe inside Markdown."""
    return " ".join(str(text).split()).replace("<", "&lt;").replace(">", "&gt;")


def _cell(text: object) -> str:
    return _safe(text).replace("|", "\\|")


def _time(stamp: object) -> str:
    return str(stamp or "").replace("T", " ").replace("+00:00", " UTC")


def _shopper(user_id: str | None) -> str:
    if not user_id:
        return "Guest"
    try:
        user = find_user_by_id(user_id)
    except StorageError:
        user = None
    return f"Signed in as `{user['username']}`" if user else f"Account `{user_id}`"


def needs_follow_up(chat: dict) -> bool:
    """Handoffs and failures need the team; an off-topic pause does not."""
    handoff = chat.get("handoff")
    return bool(handoff) and handoff.get("reason") != "off_topic"


def outcome(chat: dict) -> str:
    handoff = chat.get("handoff")
    if not handoff:
        return "Answered"
    reason_code = handoff.get("reason", "")
    reason = REASON_LABELS.get(reason_code, reason_code)
    if reason_code == "off_topic":
        return f"Paused (error 509): {reason}"
    if is_failure(reason_code):
        return f"Stopped (error {error_code(reason_code)}): {reason}"
    return f"Handed off: {reason}"


def _off_topic(chat: dict) -> int:
    return sum(1 for message in _agent_messages(chat) if (message.get("meta") or {}).get("kind") == "off_topic")


def _agent_messages(chat: dict) -> list[dict]:
    return [message for message in chat.get("messages", []) if message.get("role") == "agent"]


def _unlooked(chat: dict) -> int:
    """Answers given without any lookup, worth a reviewer's glance."""
    return sum(
        1
        for message in _agent_messages(chat)
        if (message.get("meta") or {}).get("kind") == "answer" and not (message.get("meta") or {}).get("lookups")
    )


def _cost(chat: dict) -> float:
    return sum((message.get("meta") or {}).get("est_cost_usd") or 0 for message in _agent_messages(chat))


def _reply_heading(message: dict) -> str:
    meta = message.get("meta") or {}
    kind = meta.get("kind")
    parts = [f"Assistant · {_time(message.get('time'))}"]
    if kind == "paused":
        parts.append("fixed note from the shop (assistant paused)")
    elif kind == "limit":
        parts.append("fixed note from the shop (daily cap reached)")
    elif meta.get("provider"):
        parts.append(f"{label(meta['provider'])} {meta.get('model') or ''}".strip())
        if meta.get("latency_ms") is not None:
            parts.append(f"{meta['latency_ms'] / 1000:.1f} s")
    return " · ".join(parts)


def _decided_by(handoff: dict) -> str:
    if handoff.get("by") == "assistant":
        return "the assistant"
    if handoff.get("code") == "509":
        return "the shop (safeguard)"
    return "the shop (system failure)"


def transcript(chat: dict, visit_errors: list[dict]) -> str:
    cid = chat.get("conversation_id", "")
    lines = [
        f"# Conversation {cid}",
        "",
        f"- **Started:** {_time(chat.get('created_at'))}",
        f"- **Last message:** {_time(chat.get('updated_at'))}",
        f"- **Shopper:** {_shopper(chat.get('user_id'))}",
        f"- **Browser session:** `{chat.get('session_id', '')}`",
        f"- **Outcome:** {outcome(chat)}",
        f"- **Needs follow-up:** {'Yes' if needs_follow_up(chat) else 'No'}",
        f"- **Answers given without a lookup:** {_unlooked(chat)}",
        f"- **Off-topic requests:** {_off_topic(chat)}",
        f"- **Estimated AI cost:** ${_cost(chat):.4f}",
        "",
        "Card numbers typed into the chat are removed before they are saved.",
        "",
        "## Errors during this visit",
        "",
    ]
    if visit_errors:
        for entry in reversed(visit_errors):
            code = str(entry.get("code", ""))
            lines.append(f"- {_time(entry.get('time'))} · **{code}** · {_safe(CODES.get(code, ''))} · `{_safe(entry.get('detail', ''))}`")
    else:
        lines.append("None.")
    lines += ["", "## Messages", ""]
    for message in chat.get("messages", []):
        if message.get("role") == "shopper":
            lines.append(f"### Shopper · {_time(message.get('time'))}")
            lines += ["", f"> {_safe(message.get('text', ''))}", ""]
            continue
        meta = message.get("meta") or {}
        lines += [f"### {_reply_heading(message)}", ""]
        for paragraph in str(message.get("text", "")).split("\n\n"):
            lines += [f"> {_safe(paragraph)}", ">"]
        lines[-1] = ""
        if meta.get("kind") == "off_topic":
            lines.append(f"- **Off topic:** {_safe(meta.get('topic', ''))} (declined by the shop)")
        if meta.get("kind") in ("answer", "handoff"):
            lookups = meta.get("lookups") or []
            lines.append(f"- Looked up: {', '.join(_safe(item) for item in lookups)}" if lookups else "- **Review:** no lookup for this answer.")
        if meta.get("input_tokens") or meta.get("output_tokens"):
            lines.append(
                f"- Tokens: {meta.get('input_tokens', 0):,} in ({meta.get('cached_tokens', 0):,} cached) / "
                f"{meta.get('output_tokens', 0):,} out · est. ${meta.get('est_cost_usd') or 0:.4f}"
            )
        if meta.get("error"):
            lines.append(f"- Shop stopped the assistant: {REASON_LABELS.get(meta['error'], meta['error'])}")
        lines.append("")
    handoff = chat.get("handoff")
    if handoff:
        lines += [
            "## Handoff",
            "",
            f"- **When:** {_time(handoff.get('time'))}",
            f"- **Reason:** {REASON_LABELS.get(handoff.get('reason'), handoff.get('reason', ''))}",
            f"- **Decided by:** {_decided_by(handoff)}",
            f"- **Summary:** {_safe(handoff.get('summary', '')) or '(none)'}",
            "",
        ]
    return "\n".join(lines)


def index(chats: list[dict]) -> str:
    follow_up = sorted((chat for chat in chats if needs_follow_up(chat)), key=lambda c: str(c.get("updated_at", "")), reverse=True)
    others = sorted((chat for chat in chats if not needs_follow_up(chat)), key=lambda c: str(c.get("updated_at", "")), reverse=True)
    lines = [
        "# Conversations",
        "",
        "Conversations that need follow-up come first, then the rest, newest first.",
        "",
        "| Conversation | Last message | Shopper | Outcome | Shopper messages | Answers without a lookup | Off-topic requests |",
        "|---|---|---|---|---|---|---|",
    ]
    for chat in [*follow_up, *others]:
        cid = chat.get("conversation_id")
        if not cid:
            continue
        shopper_count = sum(1 for message in chat.get("messages", []) if message.get("role") == "shopper")
        lines.append(
            f"| [{cid}]({cid}.md) | {_cell(_time(chat.get('updated_at')))} | {_cell(_shopper(chat.get('user_id')))} "
            f"| {_cell(outcome(chat))} | {shopper_count} | {_unlooked(chat)} | {_off_topic(chat)} |"
        )
    return "\n".join(lines) + "\n"


def write_records(session_id: str) -> None:
    """Rewrite this visit's transcript and the index. Raises OSError or
    StorageError on failure; the caller decides how to report it."""
    chats = all_chats()
    chat = next((item for item in chats if item.get("session_id") == session_id), None)
    if chat and chat.get("conversation_id"):
        write_text_file(TRANSCRIPTS_DIR / f"{chat['conversation_id']}.md", transcript(chat, errors_for_session(session_id)))
    write_text_file(INDEX_PATH, index(chats))
