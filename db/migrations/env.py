import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from logging.config import fileConfig
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.database import Base
from app.models import *
from app.core.config import get_settings

load_dotenv(os.path.join(BASE_DIR, ".env"))

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata

settings = get_settings()
DATABASE_URL = settings.DATABASE_URL

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required")


def get_sync_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
    if database_url.startswith("sqlite+aiosqlite:///"):
        return database_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    return database_url

SYNC_DATABASE_URL = get_sync_database_url(DATABASE_URL)

# Create sqlite db directory if needed
if "sqlite://" in SYNC_DATABASE_URL:
    db_dir = Path(BASE_DIR) / "data" / "db"
    db_dir.mkdir(parents=True, exist_ok=True)


def run_migrations_offline():
    context.configure(
        url=SYNC_DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        {"sqlalchemy.url": SYNC_DATABASE_URL},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
