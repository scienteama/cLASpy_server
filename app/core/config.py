from functools import lru_cache
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    app_name: str = "cLASpy_Server"

    db_user: str | None = None
    db_password: str | None = None
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str | None = None

    ENV: str = "development"
    PORT: int = 8000
    HOST: str = "localhost"

    SECRET_KEY: str | None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    UPLOAD_DIR: str = "data/root"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def PROJECT_ROOT(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def DATABASE_URL(self) -> str:
        if self.db_user and self.db_password and self.db_name:
            return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        return "sqlite+aiosqlite:///./dev.db"


@lru_cache()
def get_settings() -> Settings:
    """Retourne une instance unique de Settings."""
    return Settings()
