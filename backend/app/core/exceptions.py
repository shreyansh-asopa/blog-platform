"""Domain errors raised by services and mapped to HTTP responses in one place.

Services raise these instead of HTTP exceptions, so business logic stays unaware of HTTP.
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_request_id


class AppError(Exception):
    status_code = 400
    code = "bad_request"
    headers: dict[str, str] | None = None

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class AuthenticationError(AppError):
    status_code = 401
    code = "not_authenticated"
    headers = {"WWW-Authenticate": "Bearer"}


class PermissionDeniedError(AppError):
    status_code = 403
    code = "permission_denied"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class ContentRejectedError(AppError):
    status_code = 422
    code = "content_rejected"


class FileTooLargeError(AppError):
    status_code = 413
    code = "file_too_large"


class UnsupportedFileTypeError(AppError):
    status_code = 415
    code = "unsupported_file_type"


class RateLimitedError(AppError):
    status_code = 429
    code = "rate_limited"

    def __init__(self, message: str, retry_after: float):
        super().__init__(message)
        # Tells the client how many seconds to wait before trying again
        self.headers = {"Retry-After": str(max(1, round(retry_after)))}


def error_response(
    status_code: int,
    code: str,
    message: str,
    headers: dict[str, str] | None = None,
    **extra: Any,
) -> JSONResponse:
    """The one error shape the API uses: {"error": {"code", "message", "request_id", ...}}.

    The request_id lets a user quote an error and us find its log lines.
    """
    body = {"code": code, "message": message, "request_id": get_request_id(), **extra}
    return JSONResponse(status_code=status_code, content={"error": body}, headers=headers)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return error_response(exc.status_code, exc.code, exc.message, exc.headers)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Bad input (a missing field, a too-long title...) in the same shape as every other error."""
    details = [
        # e.g. {"field": "body.title", "message": "String should have at most 200 characters"}
        {"field": ".".join(str(part) for part in error["loc"]), "message": error["msg"]}
        for error in exc.errors()
    ]
    return error_response(422, "validation_error", "The request is invalid", details=details)


_HTTP_CODES = {404: "not_found", 405: "method_not_allowed"}


async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Errors raised by the framework itself, such as an unknown URL."""
    code = _HTTP_CODES.get(exc.status_code, "http_error")
    return error_response(exc.status_code, code, str(exc.detail), exc.headers)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
