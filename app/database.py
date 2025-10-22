from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from databases import Database
from app.core.config import settings
from typing import Generator

database = Database(settings.DATABASE_URL)
metadata = MetaData()

engine = create_engine(
    settings.DATABASE_URL.replace("asyncpg", "psycopg2"),
    echo=True
)

Base = declarative_base()

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        db.close()
