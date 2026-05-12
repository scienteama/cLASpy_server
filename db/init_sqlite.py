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


async def init_sqlite():
    settings = get_settings()

    if settings.ENV != "desktop":
        print(f"This script is for desktop mode only. Current ENV={settings.ENV}")
        return

    print(f"Initializing SQLite database: {settings.DATABASE_URL}")

    # Create all tables from Base metadata
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("✅ SQLite database initialized successfully!")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_sqlite())
