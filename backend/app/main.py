from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx2
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.api.v1.routes import health
from app.core.config import Settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.rate_limit import RateLimiter
from app.db.session import create_engine, create_sessionmaker
from app.integrations.moderation import create_moderator
from app.integrations.storage import LocalStorage
from app.middleware.request_context import RequestContextMiddleware


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings.log_level, settings.log_format)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_engine(settings)
        app.state.sessionmaker = create_sessionmaker(engine)
        # One HTTP client for the app's lifetime: it keeps connections open between calls
        async with httpx2.AsyncClient(timeout=settings.moderation_timeout_seconds) as http:
            app.state.moderator = create_moderator(settings, http)
            yield
        await engine.dispose()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.settings = settings
    app.state.storage = LocalStorage(settings.upload_dir)
    app.state.rate_limiter = RateLimiter()
    register_exception_handlers(app)

    # Each add_middleware wraps everything added before it, so the last one added runs
    # first. A request passes through: request id/logging -> CORS -> GZip -> the routes
    app.add_middleware(GZipMiddleware, minimum_size=1000)  # small bodies aren't worth it
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        # Logins use a bearer token, not cookies, so browsers needn't send credentials
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        # Response headers the frontend's JavaScript is allowed to read
        expose_headers=["X-Request-ID", "Retry-After", "Content-Disposition"],
    )
    app.add_middleware(RequestContextMiddleware)

    # Ops endpoints sit at the root so Docker health checks don't depend on the API version
    app.include_router(health.router)
    app.include_router(api_router)
    # Serves the uploaded files themselves. With S3 this mount goes away: files get S3 URLs
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

    return app


app = create_app()
