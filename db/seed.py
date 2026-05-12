import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import engine
from app.models.user import User, UserStorage
from app.models.role import Role
from app.utils.auth_utils import hash_password
from dotenv import load_dotenv


load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

ENV = os.getenv("ENV")


async def seed():
    async_session = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # ---- Roles par défaut ----
        roles_data = [
            {"name": "admin", "description": "Accès complet"},
            {"name": "poweruser", "description": "Peut gérer certains projets"},
            {"name": "user", "description": "Utilisateur classique"},
            {"name": "viewer", "description": "Lecture seule"},
        ]

        GB = 1024 ** 3
        ROLE_MAX_SPACE = {
            "viewer": 1 * GB,
            "user": 2 * GB,
            "poweruser": 5 * GB,
            "admin": None,
        }

        for r in roles_data:
            exists = await session.scalar(select(Role).where(Role.name == r["name"]))
            if not exists:
                session.add(Role(name=r["name"],
                                 description=r["description"],
                                 max_space=ROLE_MAX_SPACE[r["name"]]))

        await session.commit()

        # ---- Utilisateurs par défaut ----
        DEFAULT_USERS = {
            "admin": ("Admin", "System"),
            "poweruser": ("Power", "User"),
            "user": ("Basic", "User"),
            "viewer": ("Read", "Only"),
        }

        BASE_PASSWORD = "Azerty1234!"

        users_data = [
            {
                "firstname": fn,
                "lastname": ln,
                "email": f"{role}@claspy.{ENV[0:3]}",
                "password": BASE_PASSWORD,
                "role_name": role,
            }
            for role, (fn, ln) in DEFAULT_USERS.items()
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
                await session.flush()

                user_storage = UserStorage(
                    user_id=user.id
                )

                session.add(user_storage)

        await session.commit()

        print("✅ Database seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed())
