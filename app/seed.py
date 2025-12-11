# app/seed.py
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
from app.models.project import Project, ProjectTeam
from app.models.role import Role
from app.services.files_service import FileService
from app.utils.auth_utils import hash_password

async def seed():
    async_session = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # ---- 1. Roles par défaut ----
        roles_data = [
            {"name": "admin", "description": "Accès complet"},
            {"name": "poweruser", "description": "Peut gérer certains projets"},
            {"name": "user", "description": "Utilisateur classique"},
            {"name": "viewer", "description": "Lecture seule"},
        ]

        roles = []
        for r in roles_data:
            role = Role(name=r["name"], description=r["description"])
            session.add(role)
            roles.append(role)

        await session.commit()

        # ---- 2. Utilisateurs par défaut ----
        users_data = [
            {"firstname": "Alice", "lastname": "Admin", "email": "alice@example.com", "password": "Azerty1234!", "role_id": 1},
            {"firstname": "Bob", "lastname": "Power", "email": "bob@example.com", "password": "Azerty1234!", "role_id": 2},
            {"firstname": "Charlie", "lastname": "User", "email": "charlie@example.com", "password": "Azerty1234!", "role_id": 3},
        ]

        users = []
        for u in users_data:
            user = User(
                firstname=u["firstname"],
                lastname=u["lastname"],
                email=u["email"],
                password=hash_password(u["password"]),
                role_id=u["role_id"],
                created_at=datetime.now()
            )
            session.add(user)
            users.append(user)

        await session.commit()

        # ---- 3. Projets par défaut ----
        projects_data = [
            {"name": "ML Exemple 1", "description": "Exemple 1 de projet ML"},
            {"name": "ML Exemple 2", "description": "Exemple 2 de projet ML"}
        ]

        projects = []
        for p in projects_data:
            project = Project(name=p["name"], description=p["description"])
            session.add(project)
            projects.append(project)

        await session.commit()

        # ---- 4. Assignation utilisateurs -> projets ----
        assignments_data = [
            {"project_name": "ML Exemple 1", "user_email": "alice@example.com", "role_id": 1},
            {"project_name": "ML Exemple 1", "user_email": "bob@example.com", "role_id": 2},
            {"project_name": "ML Exemple 1", "user_email": "charlie@example.com", "role_id": 3},
            {"project_name": "ML Exemple 2", "user_email": "bob@example.com", "role_id": 4},
        ]

        for a in assignments_data:
            project_id = await session.scalar(
                Project.__table__.select().where(Project.name == a["project_name"])
            )
            user_id = await session.scalar(
                User.__table__.select().where(User.email == a["user_email"])
            )
           
            assignment = ProjectTeam(project_id=project_id, user_id=user_id, role_id=a["role_id"])
            session.add(assignment)

        await session.commit()

        await create_users_directories(session)

        print("✅ Base remplie avec succès !")

async def create_users_directories(db: AsyncSession):
    try:
        config = get_settings()
        stmt = select(User)
        result = await db.execute(stmt)
        users : List[User] = result.scalars().all()

        for u in users:
            folder_name = f"{u.id}_{u.firstname[0].lower()}{u.lastname.lower()}"
            base_dir = Path(config.UPLOAD_DIR)
            user_dir = (base_dir / "users" / folder_name).resolve()
            user_dir.mkdir(parents=True, exist_ok=True)

    except Exception as e:
        print (f"Une erreur est survenue : {e}")


if __name__ == "__main__":
    asyncio.run(seed())
