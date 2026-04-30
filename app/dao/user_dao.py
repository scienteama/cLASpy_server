from http import HTTPStatus
from typing import Any, Dict, List
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User, UserStorage
from app.utils.db_error import catch_db_errors


class UserDAO:

    def __init__(self, db: AsyncSession):
        self.db = db

    @catch_db_errors(message_model="Erreur lors de la création de l'utilisateur")
    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    @catch_db_errors(message_model="Erreur lors de la mise à jour de l'utilisateur")
    async def update(self, user_id: int, update_data: Dict[str, Any]) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user: User | None = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Utilisateur introuvable")

        for field, value in update_data.items():
            setattr(user, field, value)

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    @catch_db_errors(message_model="Erreur lors de la suppression de l'utilisateur")
    async def delete(self, user_id: int) -> bool:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user: User | None = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail=f"Utilisateur {user_id} introuvable"
            )
        await self.db.delete(user)
        return True

    async def get_by_id(self, user_id: int) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user: User | None = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail=f"Utilisateur {user_id} introuvable"
            )
        return user

    async def get_user_storage_by_user_id(self, user_id: int) -> UserStorage:
        result = await self.db.execute(select(UserStorage).where(UserStorage.user_id == user_id))
        user_storage: UserStorage | None = result.scalar_one_or_none()
        if not user_storage:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND)
        return user_storage

    async def get_by_email(self, email: str) -> User:
        result = await self.db.execute(select(User).where(User.email == email))
        user: User | None = result.scalar_one_or_none()
        return user

    async def get_all_users(self) -> List[User]:
        result = await self.db.execute(select(User))
        users: List[User] = result.scalars().all()
        return users
