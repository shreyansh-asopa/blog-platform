from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx2
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.api.v1.routes import health
from app.core.config import Settings
from app.core.exceptions import register_exception_handlers
from app.db.session import create_engine, create_sessionmaker
from app.integrations.moderation import create_moderator
from app.integrations.storage import LocalStorage


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

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
    register_exception_handlers(app)

    # Ops endpoints sit at the root so Docker health checks don't depend on the API version
    app.include_router(health.router)
    app.include_router(api_router)
    # Serves the uploaded files themselves. With S3 this mount goes away: files get S3 URLs
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

    return app


app = create_app()
