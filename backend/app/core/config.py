from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.logging import LogFormat

# The .env file lives at the repo root, shared with docker-compose.yml
REPO_ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"

# The model each AI provider uses unless AI_MODEL says otherwise
DEFAULT_MODELS = {"claude": "claude-sonnet-5", "ollama": "llama3.1:8b"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT_ENV, extra="ignore")

    app_name: str = "Lumen API"

    # "json" for machines (Docker, log search tools), "console" for reading in a terminal
    log_format: LogFormat = "json"
    log_level: str = "INFO"

    # Web pages allowed to call the API from a browser. Set in .env as a JSON list:
    # CORS_ORIGINS=["https://lumen.example"]
    cors_origins: list[str] = ["http://localhost:5173"]

    # Rate limits, per minute. Login counts attempts per IP address and username
    login_attempts_per_minute: int = 5
    comments_per_minute: int = 10

    postgres_user: str
    postgres_password: str
    postgres_db: str
    # Separate database the test suite runs against
    postgres_test_db: str = "blog_test"
    # "localhost" when running on your machine, "db" inside Docker Compose
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # Signs login tokens. Generate with: openssl rand -hex 32
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Comment moderation. Without a URL the built-in word list is used.
    # With one, comments are sent to that API (see app/integrations/moderation.py)
    moderation_api_url: str | None = None
    moderation_api_key: str | None = None
    moderation_timeout_seconds: float = 3.0
    moderation_retries: int = 2

    # Uploaded files (post covers). Relative paths are resolved from where the app starts:
    # backend/uploads locally, /app/uploads (a Docker volume) in the container
    upload_dir: Path = Path("uploads")
    max_cover_bytes: int = 5 * 1024 * 1024

    # AI writing help in the editor (see app/integrations/ai.py). "claude" uses Anthropic's
    # API and needs a key; "ollama" is free, a model run on this machine; "off" hides it
    ai_provider: Literal["claude", "ollama", "off"] = "claude"
    # Empty means the provider's default (DEFAULT_MODELS)
    ai_model: str = ""
    # From https://console.anthropic.com. Posts are sent to Anthropic to get suggestions
    anthropic_api_key: str | None = None
    anthropic_url: str = "https://api.anthropic.com"
    # Inside Docker Compose this is http://host.docker.internal:11434, the Mac itself
    ollama_url: str = "http://localhost:11434"
    # How much text a local model reads and writes at once, in tokens (about 4 characters each)
    ai_context_tokens: int = 8192
    # Posts longer than this don't fit in a local model's window with room for the answer
    ai_max_chars: int = 12_000
    # A local model is slow the first time, while it loads into memory
    ai_timeout_seconds: float = 180.0
    ai_requests_per_minute: int = 6

    @property
    def model_name(self) -> str:
        return self.ai_model or DEFAULT_MODELS.get(self.ai_provider, "")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
