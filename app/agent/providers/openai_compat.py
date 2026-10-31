"""Any model server that speaks OpenAI's chat completions API.

Ollama serves one at OLLAMA_URL/v1, and OpenAI (or Gemini, through its own
compatibility endpoint) can reuse this class with a different URL and key.
Claude does not: Anthropic's compatibility endpoint drops prompt caching,
effort, and refusal details, so Claude gets a native provider. See
docs/agent-setups.md.

No sampling settings are sent. Ollama's live in the files in ollama/, and
some hosted models reject them.
"""

import json

import openai

from ..settings import AgentSettings
from .base import (
    MAX_TOOL_ROUNDS,
    ProviderRefused,
    ProviderReply,
    ProviderUnavailable,
    ToolLoopLimit,
    ToolRunner,
)

# Output cap for one model call, including a model's thinking. Replies are a few
# sentences, but Gemma 4 used up to 878 tokens on one reply in testing, so this
# leaves room. A model that runs past it is stuck, and a cut-off answer is handed
# off rather than shown. Ollama honors `max_tokens` but ignores
# `max_completion_tokens`.
MAX_OUTPUT_TOKENS = 2048
TIMEOUT_SECONDS = 60


class OpenAICompatProvider:
    def __init__(
        self,
        name: str,
        label: str,
        base_url: str,
        api_key: str,
        price_per_mtok: tuple[float, float] = (0.0, 0.0),
    ):
        """`price_per_mtok` is (input, output) US dollars per million tokens;
        a local model costs nothing."""
        self.name = name
        self.label = label
        self.base_url = base_url
        self.price_per_mtok = price_per_mtok
        # No retries: a shopper waiting on a stuck server is better served by a quick handoff.
        self._client = openai.OpenAI(base_url=base_url, api_key=api_key, timeout=TIMEOUT_SECONDS, max_retries=0)

    def reply(
        self,
        system: str,
        tools: list[dict],
        messages: list[dict],
        runner: ToolRunner,
        settings: AgentSettings,
    ) -> ProviderReply:
        chat = [{"role": "system", "content": system}]
        chat += [{"role": message["role"], "content": message["text"]} for message in messages]
        specs = [{"type": "function", "function": spec} for spec in tools]
        total = ProviderReply(text="", est_cost_usd=0.0)
        rounds = 0
        while True:
            completion = self._complete(settings.model, chat, specs)
            self._count(completion, total, runner, settings)
            choice = completion.choices[0]
            message = choice.message
            if choice.finish_reason == "length":
                raise ProviderUnavailable("provider_error", f"reply cut off at {MAX_OUTPUT_TOKENS} tokens")
            if choice.finish_reason == "content_filter" or message.refusal:
                raise ProviderRefused()
            if not message.tool_calls:
                total.text = message.content or ""
                return total
            if rounds == MAX_TOOL_ROUNDS:
                raise ToolLoopLimit()
            rounds += 1
            chat.append(
                {
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [call.model_dump() for call in message.tool_calls],
                }
            )
            for call in message.tool_calls:
                result, _is_error = runner.run(call.function.name, _arguments(call.function.arguments))
                chat.append({"role": "tool", "tool_call_id": call.id, "content": result})
                if runner.done:
                    return total

    def _complete(self, model: str, chat: list[dict], specs: list[dict]):
        try:
            return self._client.chat.completions.create(
                model=model,
                messages=chat,
                tools=specs,
                max_tokens=MAX_OUTPUT_TOKENS,
            )
        except openai.APITimeoutError as exc:
            raise ProviderUnavailable("provider_error", f"{self.label} timed out after {TIMEOUT_SECONDS}s") from exc
        except openai.APIConnectionError as exc:
            raise ProviderUnavailable("provider_error", f"{self.label} unreachable at {self.base_url}") from exc
        except openai.NotFoundError as exc:
            raise ProviderUnavailable("provider_error", f"model not found: {model}") from exc
        except openai.APIStatusError as exc:
            raise ProviderUnavailable("provider_error", f"HTTP {exc.status_code}: {str(exc)[:200]}") from exc

    def _count(self, completion, total: ProviderReply, runner: ToolRunner, settings: AgentSettings) -> None:
        usage = completion.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        details = usage.prompt_tokens_details if usage else None
        price_in, price_out = self.price_per_mtok
        cost = (input_tokens * price_in + output_tokens * price_out) / 1_000_000
        total.input_tokens += input_tokens
        total.output_tokens += output_tokens
        total.cached_tokens += (details.cached_tokens or 0) if details else 0
        total.est_cost_usd += cost
        runner.charge_tokens(input_tokens, output_tokens, settings.max_tokens_per_reply, cost)


def _arguments(raw: str | None) -> object:
    """The model's JSON arguments. Anything unparseable reaches the runner as
    a non-dict, which it treats as no arguments and reports back."""
    try:
        return json.loads(raw or "{}")
    except json.JSONDecodeError:
        return None
