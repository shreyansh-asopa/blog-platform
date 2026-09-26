import re
import time
import uuid

import structlog
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.exceptions import error_response

logger = structlog.get_logger("app.access")

# A caller may send its own X-Request-ID to trace a request across services. Only short,
# plain ids are kept, so nobody can smuggle fake log lines or huge values into our logs
_VALID_ID = re.compile(r"[A-Za-z0-9._-]{1,64}")

# Docker calls these every few seconds; logging each success would bury everything else
_QUIET_PATHS = {"/health", "/ready"}


class RequestContextMiddleware:
    """Gives every request an id, logs one line per request, and turns crashes into clean 500s.

    Written as plain ASGI (a function of scope/receive/send) rather than Starlette's
    BaseHTTPMiddleware, so streamed responses like the CSV export pass straight through.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = dict(scope["headers"]).get(b"x-request-id", b"").decode("latin-1")
        request_id = incoming if _VALID_ID.fullmatch(incoming) else uuid.uuid4().hex
        # Everything logged from here until the response is sent carries this id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        started = time.perf_counter()
        status = 500
        response_started = False

        async def send_with_id(message: Message) -> None:
            nonlocal status, response_started
            if message["type"] == "http.response.start":
                response_started = True
                status = message["status"]
                MutableHeaders(scope=message).append("X-Request-ID", request_id)
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        except Exception:
            logger.exception("unhandled_error")
            if response_started:
                # Part of the response is already on its way; nothing sensible can be sent
                raise
            # Never show the traceback to the client: it can reveal code and data
            response = error_response(500, "internal_error", "Something went wrong on our side")
            await response(scope, receive, send_with_id)
        finally:
            if scope["path"] not in _QUIET_PATHS or status >= 400:
                logger.info(
                    "request",
                    method=scope["method"],
                    path=scope["path"],
                    status=status,
                    duration_ms=round((time.perf_counter() - started) * 1000, 1),
                    client=scope["client"][0] if scope.get("client") else None,
                )
