from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    db_user: str | None = None
    db_password: str | None = None
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str | None = None

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @property
    def PROJECT_ROOT(self) -> Path:
        """
        Retourne la racine du projet.

        """
        return Path(__file__).resolve().parents[2]
    #DYNAMIC_PLUGINS_FILE = PROJECT_ROOT / "dynamic_plugins.txt"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def DATABASE_URL(self) -> str:
        if self.db_user and self.db_password and self.db_name:
            return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        return "sqlite+aiosqlite:///./dev.db"

settings = Settings()