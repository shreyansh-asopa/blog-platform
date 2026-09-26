from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# The .env file lives at the repo root, shared with docker-compose.yml
REPO_ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT_ENV, extra="ignore")

    app_name: str = "Blog Platform API"

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

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
