from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import MetaData
from app.core.config import settings
from typing import AsyncGenerator

# URL de connexion async
DATABASE_URL = settings.DATABASE_URL  

# Création de l'engine async
engine = create_async_engine(DATABASE_URL, echo=False)

async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

metadata = MetaData()
Base = declarative_base()

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
