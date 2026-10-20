"""A browser session id that outlives sign-in and ends when the browser closes."""

import uuid

from starlette.datastructures import MutableHeaders
from starlette.requests import Request

COOKIE_NAME = "lumen_sid"


def new_session_id() -> str:
    return str(uuid.uuid4())


def valid_session_id(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = uuid.UUID(value)
    except ValueError:
        return None
    if parsed.version != 4 or str(parsed) != value:
        return None
    return value


def shop_session_id(request: Request) -> str | None:
    value = valid_session_id(request.scope.get("shop_session_id"))
    return value


class ShopSessionMiddleware:
    """Assign lumen_sid on the first request and keep it until the browser closes.

    The cookie has no Max-Age, so it is dropped when the browser session ends.
    Sign-in and sign-out do not change it.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        existing = valid_session_id(request.cookies.get(COOKIE_NAME))
        session_id = existing or new_session_id()
        scope["shop_session_id"] = session_id

        async def send_with_cookie(message):
            if message["type"] == "http.response.start" and existing is None:
                headers = MutableHeaders(scope=message)
                headers.append(
                    "Set-Cookie",
                    f"{COOKIE_NAME}={session_id}; Path=/; HttpOnly; SameSite=Lax",
                )
            await send(message)

        await self.app(scope, receive, send_with_cookie)
