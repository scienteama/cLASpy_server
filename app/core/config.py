from functools import lru_cache
import os
import tomllib
from pydantic_settings import BaseSettings
from pathlib import Path
from art import text2art


class Settings(BaseSettings):
    app_name: str = "cLASpy_Server"

    db_user: str | None = None
    db_password: str | None = None
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str | None = None
    database_url: str | None = None

    ENV: str = "development"
    PORT: int = 8000
    HOST: str = "localhost"

    ALLOWED_ORIGINS: list[str] = [
        "https://localhost:8081",
        "https://127.0.0.1:8081",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

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
                "database_url",
                "SECRET_KEY",
                "ALGORITHM",
            }
        )

    @property
    def DATABASE_URL(self) -> str:
        if self.database_url:
            return self.database_url

        if self.ENV == "desktop":
            db_path = (self.PROJECT_ROOT / "data" / "db" / "desktop.db").resolve()
            return f"sqlite+aiosqlite:///{db_path.as_posix()}"

        if not self.db_user or not self.db_password or not self.db_name:
            raise ValueError(
                "DATABASE_URL is not set and PostgreSQL credentials are incomplete. "
                "Define DATABASE_URL or the required db_user/db_password/db_name values."
            )

        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    def get_log_config(self):
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": "uvicorn.logging.DefaultFormatter",
                    "fmt": "%(asctime)s | %(levelprefix)s %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
                "access": {
                    "()": "uvicorn.logging.AccessFormatter",
                    "fmt": '%(asctime)s | %(levelprefix)s [Access] "%(request_line)s" %(status_code)s',
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                },
                "access": {
                    "class": "logging.StreamHandler",
                    "formatter": "access",
                },
            },
            "loggers": {
                "uvicorn.error": {
                    "handlers": ["default"],
                    "level": "INFO",
                    "propagate": False,
                },
                "uvicorn.access": {
                    "handlers": ["access"],
                    "level": "INFO",
                    "propagate": False,
                },
                "app": {
                    "handlers": ["default"],
                    "level": "INFO",
                    "propagate": False,
                },
            },
        }


def print_banner():

    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)

    app_version = data["project"]["version"]
    description = data["project"]["description"]

    print("======================================================================")
    print(
        text2art(
            "CLASPY-T",
            space=1,
        )
    )
    print(f" Version : {app_version}")
    print(f" Description : {description}")
    print(f" Env : {os.getenv('ENV', 'development')}")
    print("======================================================================")


@lru_cache()
def get_settings() -> Settings:
    """Retourne une instance unique de Settings."""
    return Settings()
