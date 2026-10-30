"""Who the agent is helping. Built by the server from the shopper's own
session; the model never chooses whose data it reads."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ShopperContext:
    session_id: str
    user_id: str | None
    username: str | None
    order_ids: tuple[str, ...]
    conversation_id: str
