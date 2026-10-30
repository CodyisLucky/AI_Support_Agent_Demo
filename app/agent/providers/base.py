"""What every provider implements, and the ways a reply can fail."""

from dataclasses import dataclass
from typing import Protocol

from ..settings import AgentSettings
from ..tools import ReplyBudgetExceeded, ToolRunner  # noqa: F401  (re-exported for providers)

# Rounds of tool calls allowed in one reply before the shop stops and hands off.
MAX_TOOL_ROUNDS = 6


class ProviderUnavailable(Exception):
    """The provider cannot answer: not connected, no key, unreachable, or erroring.

    `reason` is "not_connected" or "provider_error". `detail` goes to the
    error log, never to the shopper.
    """

    def __init__(self, reason: str, detail: str):
        self.reason = reason
        self.detail = detail
        super().__init__(detail)


class ProviderRefused(Exception):
    """The provider declined to answer."""


class ToolLoopLimit(Exception):
    """The model kept looking things up without answering."""


@dataclass
class ProviderReply:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    est_cost_usd: float | None = None


class Provider(Protocol):
    name: str
    label: str

    def reply(
        self,
        system: str,
        tools: list[dict],
        messages: list[dict],
        runner: ToolRunner,
        settings: AgentSettings,
    ) -> ProviderReply:
        """Answer the last message in `messages` (dicts with role "user" or
        "assistant" and text). Run tool calls through `runner`, stop as soon
        as `runner.done` is true, call `runner.charge_tokens(input, output,
        settings.max_tokens_per_reply, cost_usd)` after every model call, and raise
        ToolLoopLimit after MAX_TOOL_ROUNDS."""
        ...
