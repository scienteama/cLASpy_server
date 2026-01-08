import asyncio
from datetime import datetime
from pathlib import Path
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.database import engine
from app.models.user import User
from app.models.role import Role
from app.utils.auth_utils import hash_password


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
            {"firstname": "User", "lastname": "Admin", "email": "useradmin@example.com", "password": "Azerty1234!", "role_name": "admin"},
            {"firstname": "User", "lastname": "Power", "email": "userpower@example.com", "password": "Azerty1234!", "role_name": "poweruser"},
            {"firstname": "User", "lastname": "User", "email": "user@example.com", "password": "Azerty1234!", "role_name": "user"},
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
                    created_at=datetime.now()
                )
                session.add(user)

        await session.commit()

        # ---- Créer les dossiers utilisateurs ----
        await create_users_directories(session, config)

        print("✅ Base remplie avec succès !")


async def create_users_directories(db: AsyncSession, config):
    stmt = select(User)
    result = await db.execute(stmt)
    users: List[User] = result.scalars().all()

    for u in users:
        folder_name = f"{u.id}_{u.firstname[0].lower()}{u.lastname.lower()}"
        user_dir = Path(config.UPLOAD_DIR) / "users" / folder_name
        user_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    asyncio.run(seed())
