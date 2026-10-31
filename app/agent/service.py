"""One reply from the support agent, or an honest handoff.

The shop decides when to stop, not only the model: a provider error, a
refusal, a failed records lookup, or a run of lookups without an answer all
end in a handoff written by the shop and a 508 in the error log. Safeguards
(too many tokens for one reply, repeated off-topic requests) log 509.
"""

import re
import time
from dataclasses import dataclass

from app.errors import log_error

from .context import ShopperContext
from .handoff import error_code, handoff_text, off_topic_text, opening_for, paused_text
from .prompt import SYSTEM_PROMPT
from .providers import get_provider
from .providers.base import MAX_TOOL_ROUNDS, ProviderRefused, ProviderUnavailable, ToolLoopLimit
from .settings import AgentSettings
from .tools import TOOL_SPECS, ReplyBudgetExceeded, ToolFailure, ToolRunner

MAX_FAILURE_SUMMARY = 300


@dataclass
class AgentAnswer:
    text: str
    meta: dict
    handoff: dict | None = None


def answer(
    context: ShopperContext,
    history: list[dict],
    text: str,
    settings: AgentSettings,
    handed_off: bool = False,
    off_topic_count: int = 0,
) -> AgentAnswer:
    """Reply to `text`. `history` is earlier turns as {"role", "text"} dicts.

    Once a chat has been handed off the model is not called again; the
    shopper gets a fixed note and their message stays in the record.
    `off_topic_count` is how many earlier messages in this chat were off
    topic; reaching AGENT_OFF_TOPIC_LIMIT pauses the assistant.
    """
    if handed_off:
        return AgentAnswer(paused_text(settings, context.conversation_id), {"kind": "paused"})

    meta = {"kind": "answer", "provider": settings.provider, "model": settings.model}
    runner = ToolRunner(context)
    started = time.monotonic()
    try:
        provider = get_provider(settings)
        reply = provider.reply(
            SYSTEM_PROMPT,
            TOOL_SPECS,
            [*history, {"role": "user", "text": text}],
            runner,
            settings,
        )
    except ProviderUnavailable as exc:
        return _failure(exc.reason, exc.detail, context, text, settings, meta, runner, started)
    except ProviderRefused:
        return _failure("refusal", "provider declined", context, text, settings, meta, runner, started)
    except ToolLoopLimit:
        return _failure("loop_limit", f"{MAX_TOOL_ROUNDS} tool rounds", context, text, settings, meta, runner, started)
    except ToolFailure as exc:
        return _failure("tool_error", f"tool failed: {exc}", context, text, settings, meta, runner, started)
    except ReplyBudgetExceeded as exc:
        return _failure("reply_budget", f"reply token limit: {exc}", context, text, settings, meta, runner, started)
    except Exception as exc:
        return _failure("provider_error", type(exc).__name__, context, text, settings, meta, runner, started)

    meta.update(
        latency_ms=_elapsed_ms(started),
        input_tokens=reply.input_tokens,
        output_tokens=reply.output_tokens,
        cached_tokens=reply.cached_tokens,
        est_cost_usd=reply.est_cost_usd,
        lookups=runner.used,
    )
    if runner.off_topic:
        meta["kind"] = "off_topic"
        meta["topic"] = runner.off_topic
        count = off_topic_count + 1
        if count >= settings.off_topic_limit:
            return _failure("off_topic", f"off-topic limit: {count}", context, text, settings, meta, runner, started)
        return AgentAnswer(off_topic_text(settings.off_topic_limit - count), meta)
    if runner.handoff:
        chosen = runner.handoff
        meta["kind"] = "handoff"
        return AgentAnswer(
            handoff_text(opening_for(chosen["reason"], chosen["explanation"]), settings, context.conversation_id),
            meta,
            {"reason": chosen["reason"], "summary": chosen["summary"], "by": "assistant"},
        )
    if not reply.text.strip():
        return _failure("provider_error", "empty reply", context, text, settings, meta, runner, started)
    if _looks_like_tool_call(reply.text):
        return _failure("provider_error", "reply was tool-call text", context, text, settings, meta, runner, started)
    return AgentAnswer(reply.text.strip(), meta)


# Weak models sometimes write a tool call as plain text instead of making it.
# Shoppers should never see that, and the call never ran, so hand off instead.
_TOOL_NAME = re.compile(r"\b(?:" + "|".join(re.escape(spec["name"]) for spec in TOOL_SPECS) + r")\b")
_JSON_FRAGMENT = re.compile(r'<tool_call>|\{\s*"[A-Za-z_]+"\s*:')


def _looks_like_tool_call(text: str) -> bool:
    return bool(_TOOL_NAME.search(text) or _JSON_FRAGMENT.search(text))


def _failure(
    reason: str,
    detail: str,
    context: ShopperContext,
    text: str,
    settings: AgentSettings,
    meta: dict,
    runner: ToolRunner,
    started: float,
) -> AgentAnswer:
    code = error_code(reason)
    log_error(context.user_id, code, detail=detail, session_id=context.session_id)
    if meta.get("kind") != "off_topic":
        meta["kind"] = "failure"
    meta.update(error=reason, latency_ms=meta.get("latency_ms", _elapsed_ms(started)), lookups=runner.used)
    if meta.get("est_cost_usd") is None and runner.cost_usd:
        meta["est_cost_usd"] = round(runner.cost_usd, 6)
    return AgentAnswer(
        handoff_text(opening_for(reason), settings, context.conversation_id),
        meta,
        {"reason": reason, "summary": text[:MAX_FAILURE_SUMMARY], "by": "shop", "code": code},
    )


def _elapsed_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)
