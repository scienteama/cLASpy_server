from http import HTTPStatus
from typing import Any, Dict, List
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.utils.db_error import catch_db_errors

class UserDAO:

    @catch_db_errors(message_model="Erreur lors de la création de l'utilisateur")
    async def create(self, user: User, db: AsyncSession) -> User:
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @catch_db_errors(message_model="Erreur lors de la mise à jour de l'utilisateur")
    async def update(self, user_id: int, update_data: Dict[str, Any], db: AsyncSession) -> User:
        result = await db.execute(select(User).where(User.id == user_id))
        user: User | None = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Utilisateur introuvable"
            )

        for field, value in update_data.items():
            setattr(user, field, value)

        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @catch_db_errors(message_model="Erreur lors de la suppression de l'utilisateur")
    async def delete(self, user_id: int, db: AsyncSession) -> bool:
        result = await db.execute(select(User).where(User.id == user_id))
        user: User | None = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Utilisateur {user_id} introuvable"
            )
        await db.delete(user)
        return True

    async def get_by_id(self, user_id: int, db: AsyncSession) -> User:
        result = await db.execute(select(User).where(User.id == user_id))
        user: User | None = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Utilisateur {user_id} introuvable"
            )
        return user

    async def get_by_email(self, email: str, db: AsyncSession) -> User:
        result = await db.execute(select(User).where(User.email == email))
        user: User | None = result.scalar_one_or_none()
        return user

    async def get_all_users(self, db: AsyncSession) -> List[User]:
        result = await db.execute(select(User))
        users: List[User] = result.scalars().all()
        return users
