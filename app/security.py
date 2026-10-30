"""Request guards and response headers applied to every request.

A form post from another origin is refused. SameSite cookies do not cover
this on its own: another port on localhost counts as the same site, so a
second local dev server could otherwise post as the shopper.
"""

from urllib.parse import urlparse

from starlette.datastructures import MutableHeaders
from starlette.requests import Request
from starlette.responses import PlainTextResponse

MAX_BODY_BYTES = 64 * 1024
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
        "font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; "
        "form-action 'self'; frame-ancestors 'none'"
    ),
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "same-origin",
}


def same_origin(request: Request) -> bool:
    """Browsers send Origin on every form post. Fall back to Referer, and
    allow a request with neither, such as curl."""
    source = request.headers.get("origin") or request.headers.get("referer")
    if not source:
        return True
    parsed = urlparse(source)
    return parsed.scheme == request.url.scheme and parsed.netloc == request.url.netloc


def rejection(request: Request) -> PlainTextResponse | None:
    if request.method not in UNSAFE_METHODS:
        return None
    if not same_origin(request):
        return PlainTextResponse("This request came from another site and was refused.", status_code=403)
    length = request.headers.get("content-length")
    if length is None:
        return PlainTextResponse("A request body needs a Content-Length.", status_code=411)
    if not length.isdigit() or int(length) > MAX_BODY_BYTES:
        return PlainTextResponse("That request is too large.", status_code=413)
    return None


class SecurityMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for name, value in SECURITY_HEADERS.items():
                    headers[name] = value
            await send(message)

        refused = rejection(Request(scope))
        if refused:
            await refused(scope, receive, send_with_headers)
            return
        await self.app(scope, receive, send_with_headers)
