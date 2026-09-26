"""Domain errors raised by services and mapped to HTTP responses in one place.

Services raise these instead of HTTP exceptions, so business logic stays unaware of HTTP.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code = 400
    code = "bad_request"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class AuthenticationError(AppError):
    status_code = 401
    code = "not_authenticated"


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


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    headers = {"WWW-Authenticate": "Bearer"} if isinstance(exc, AuthenticationError) else None
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
        headers=headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
