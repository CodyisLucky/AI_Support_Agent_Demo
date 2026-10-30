"""Every message a shopper sees when the assistant stops.

Handoffs say plainly what happened, that nothing was changed, how to reach
the team, and the conversation id that leads to the full transcript. System
failures use the fixed text here; when the assistant hands off by choice,
its own explanation opens the message and the same closing follows.
"""

from urllib.parse import quote

from .settings import AgentSettings

MAX_MAILTO_SUMMARY = 300

# Reasons the shop stops the assistant itself. Faults log 508; safeguards log 509.
FAILURE_OPENINGS = {
    "provider_error": "Sorry, our assistant hit a technical problem and can't answer right now.",
    "not_connected": "Sorry, our assistant isn't connected right now, so it can't answer.",
    "refusal": "Sorry, our assistant can't help with that request here.",
    "loop_limit": "I couldn't find a clear answer to that in our shop information, and I'd rather not guess.",
    "tool_error": "I couldn't load your account or order records just now, so I can't answer that accurately.",
    "reply_budget": "That question needed more lookups than I'm allowed for one reply, so I've stopped rather than guess.",
    "off_topic": (
        "This chat can only help with Lumen Beauty products, orders, and this website, "
        "so the assistant is paused after several requests about other things."
    ),
}

# Failures that come from a safeguard rather than a fault. They log 509, not 508.
SAFEGUARD_REASONS = {"reply_budget", "off_topic"}

# Reasons the assistant chooses with the hand_off tool, used when it gives
# no explanation of its own.
CHOSEN_OPENINGS = {
    "not_in_docs": "I couldn't find that in our shop information, and I'd rather not guess.",
    "needs_staff_action": "That needs a person on our team. I can't make changes like that from this chat.",
    "shopper_asked_for_person": "Of course. I'll pass you to our team.",
    "other": "I can't resolve this one here, so I'll pass you to our team.",
}

REASON_LABELS = {
    "not_in_docs": "Answer not in the docs",
    "needs_staff_action": "Needs a staff action",
    "shopper_asked_for_person": "Shopper asked for a person",
    "other": "Other",
    "provider_error": "Assistant error",
    "not_connected": "Provider not connected",
    "refusal": "Provider declined",
    "loop_limit": "Lookup limit reached",
    "tool_error": "Records could not be read",
    "reply_budget": "Reply token limit reached",
    "off_topic": "Off-topic requests",
}


def is_failure(reason: str) -> bool:
    return reason in FAILURE_OPENINGS


def _ways_to_reach(settings: AgentSettings) -> str:
    if settings.live_chat_url:
        return f"Email our team at {settings.support_email}, or use the live chat link below,"
    return f"Email our team at {settings.support_email}"


def error_code(reason: str) -> str:
    return "509" if reason in SAFEGUARD_REASONS else "508"


def off_topic_text(remaining: int) -> str:
    """The shop's reply to an off-topic message, before the chat is paused."""
    text = (
        "Sorry, I can only help with Lumen Beauty products, your orders, and problems on this website. "
        "Is there something about your shopping I can help with?"
    )
    if remaining == 1:
        text += "\n\nOne more request about something else will pause the assistant for this chat."
    return text


def daily_cap_text(settings: AgentSettings, conversation_id: str, reset: str) -> str:
    return (
        "Sorry, our assistant has reached its daily usage limit, so it can't answer right now. "
        f"It will be available again {reset}.\n\n"
        "Nothing in your account or orders was changed. "
        f"{_ways_to_reach(settings)} and include your conversation ID, {conversation_id}, if you need help sooner."
    )


def handoff_text(opening: str, settings: AgentSettings, conversation_id: str) -> str:
    return (
        f"{opening}\n\n"
        "Nothing in your account or orders was changed by this chat. "
        f"{_ways_to_reach(settings)} and include your conversation ID, {conversation_id}, "
        "so they can read this conversation.\n\n"
        "The assistant is paused for the rest of this chat."
    )


def opening_for(reason: str, explanation: str = "") -> str:
    if is_failure(reason):
        return FAILURE_OPENINGS[reason]
    return explanation or CHOSEN_OPENINGS.get(reason, CHOSEN_OPENINGS["other"])


def paused_text(settings: AgentSettings, conversation_id: str) -> str:
    return (
        "This chat has been passed to our team, so the assistant won't answer here. "
        f"Your message is saved with conversation ID {conversation_id}. "
        f"{_ways_to_reach(settings)} and include that ID."
    )


def contact(settings: AgentSettings, conversation_id: str, summary: str) -> dict:
    """What the chat panel needs to show the contact options."""
    subject = f"Help with conversation {conversation_id}"
    body = f"Conversation ID: {conversation_id}\n"
    if summary:
        body += f"What I need help with: {summary[:MAX_MAILTO_SUMMARY]}\n"
    mailto = f"mailto:{settings.support_email}?subject={quote(subject)}&body={quote(body)}"
    return {
        "conversation_id": conversation_id,
        "email": settings.support_email,
        "mailto": mailto,
        "live_chat_url": settings.live_chat_url,
    }
