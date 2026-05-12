#!/usr/bin/env python3
"""
Initialize SQLite database by creating all tables from models.
Use this instead of Alembic migrations for desktop mode.
"""

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.database import Base, engine
from app.core.config import get_settings
from app.models import *


# This script can be run directly to initialize the SQLite database and seed it with default data.
async def init_sqlite():
    settings = get_settings()
    seed = PROJECT_ROOT / "db" / "seed.py"

    # Check environment
    if settings.ENV != "desktop":
        print(f"This script is for desktop mode only. Current ENV={settings.ENV}")
        return

    # Ensure SQLite folder exists before opening the engine
    if settings.ENV == "desktop":
        db_path = Path(settings.DATABASE_URL.replace("sqlite+aiosqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if database already exists
    async with engine.begin() as conn:
        existing_db = await conn.run_sync(
            lambda sync_conn: sync_conn.dialect.has_table(sync_conn, "users")
        )

    if existing_db:
        print(
            f"SQLite database already exists at {settings.DATABASE_URL}, skipping initialization."
        )
        return

    print(f"Initializing SQLite database: {settings.DATABASE_URL}")

    # Create all tables from Base metadata
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("✅ SQLite database initialized successfully!")

    if seed.exists():
        print("Running seed script...")
        import importlib.util

        spec = importlib.util.spec_from_file_location("seed", seed)
        seed_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(seed_module)

        # Run seed with async context
        async with engine.begin() as conn:
            await seed_module.seed()

    else:
        print("No seed script found, skipping seeding.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_sqlite())
