import asyncio
from datetime import datetime, timezone
import os
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.database import engine
from app.models.user import User
from app.models.role import Role
from app.utils.auth_utils import hash_password

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


async def seed():
    async_session = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    config = get_settings()

    async with async_session() as session:
        # ---- Roles par défaut ----
        roles_data = [
            {"name": "admin", "description": "Accès complet"},
            {"name": "poweruser", "description": "Peut gérer certains projets"},
            {"name": "user", "description": "Utilisateur classique"},
            {"name": "viewer", "description": "Lecture seule"},
        ]

        for r in roles_data:
            exists = await session.scalar(select(Role).where(Role.name == r["name"]))
            if not exists:
                session.add(Role(name=r["name"], description=r["description"]))

        await session.commit()

        # ---- Utilisateurs par défaut ----
        users_data = [
            {"firstname": "User",
             "lastname": "Admin",
             "email": "useradmin@example.com",
             "password": "Azerty1234!",
             "role_name": "admin"},
            {"firstname": "User",
             "lastname": "Power",
             "email": "userpower@example.com",
             "password": "Azerty1234!",
             "role_name": "poweruser"},
            {"firstname": "User",
             "lastname": "User",
             "email": "user@example.com",
             "password": "Azerty1234!",
             "role_name": "user"},
        ]

        for u in users_data:
            exists = await session.scalar(select(User).where(User.email == u["email"]))
            if not exists:
                role = await session.scalar(select(Role).where(Role.name == u["role_name"]))
                user = User(
                    firstname=u["firstname"],
                    lastname=u["lastname"],
                    email=u["email"],
                    password=hash_password(u["password"]),
                    role_id=role.id,
                    created_at=datetime.now(timezone.utc)
                )
                session.add(user)

        await session.commit()

        print("✅ Base initialisée avec succès !")

if __name__ == "__main__":
    asyncio.run(seed())
