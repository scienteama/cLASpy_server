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

    ALLOWED_ORIGINS: list[str] = ["https://localhost:8081", "https://127.0.0.1:8081"]

    SECRET_KEY: str | None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    UPLOAD_DIR: str = "data/storage"
    TEMP_DIR: str = "data/storage/temp"
    TRASH_DIR: str = "data/storage/trash"
    RECOVERY_DIR: str = "data/storage/recovery"
    DEFAULT_OUTPUT_DIR: str = "data/storage/outputs"

    RABBITMQ_DEFAULT_USER: str | None
    RABBITMQ_DEFAULT_PASS: str | None
    REDIS_PASSWORD: str | None
    SERVICE_TOKEN: str | None
    FLOWER_USER: str | None
    FLOWER_PWD: str | None

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def PROJECT_ROOT(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def get_public_settings(self) -> dict:
        """Retourne les paramètres publics, excluant les champs sensibles."""
        return self.model_dump(
            exclude={
                "db_user",
                "db_password",
                "db_port",
                "db_host",
                "db_name",
                "SECRET_KEY",
                "ALGORITHM",
            }
        )


@lru_cache()
def get_settings() -> Settings:
    """Retourne une instance unique de Settings."""
    return Settings()
