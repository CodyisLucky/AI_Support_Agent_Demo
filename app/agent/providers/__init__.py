"""Which provider answers, chosen by AGENT_PROVIDER in agent.env.

The local Ollama model answers through the OpenAI-compatible provider (6c).
Claude gets its own native provider in step 6b. OpenAI and Gemini are
connected later; until a provider is built, choosing it gives an honest
"not connected" handoff instead of an error page.
"""

from ..settings import AgentSettings, secret
from .base import Provider, ProviderUnavailable
from .openai_compat import OpenAICompatProvider

LABELS = {
    "anthropic": "Claude",
    "ollama": "Local model",
    "openai": "OpenAI",
    "gemini": "Gemini",
}

# The key each cloud provider needs in .env.
API_KEYS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


def label(provider: str) -> str:
    return LABELS.get(provider, provider or "No provider")


def get_provider(settings: AgentSettings) -> Provider:
    name = settings.provider
    if name not in LABELS:
        raise ProviderUnavailable("provider_error", f"unknown provider: {name}")
    key = API_KEYS.get(name)
    if key and not secret(key):
        raise ProviderUnavailable("provider_error", f"missing {key}")
    if name == "ollama":
        # Ollama ignores the key, but the client requires one.
        return OpenAICompatProvider(name, LABELS[name], settings.ollama_url.rstrip("/") + "/v1", "ollama")
    raise ProviderUnavailable("not_connected", f"provider not connected: {name}")
