from http import HTTPStatus
from typing import Any, Dict, List
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User

class UserDAO:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user: User) -> User:
        self.db.add(user)
        try:
            await self.db.commit()
            await self.db.refresh(user)
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la création de l'utilisateur: {str(e)}"
            )
        return user

    async def update(self, user_id: int, update_data: Dict[str, Any]) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user: User | None = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Utilisateur {user_id} introuvable"
            )

        for field, value in update_data.items():
            setattr(user, field, value)

        self.db.add(user)
        try:
            await self.db.commit()
            await self.db.refresh(user)
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la mise à jour de l'utilisateur: {str(e)}"
            )
        return user

    async def delete(self, user_id: int) -> str:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user: User | None = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Utilisateur {user_id} introuvable"
            )

        try:
            await self.db.delete(user)
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la suppression de l'utilisateur: {str(e)}"
            )
        return f"Utilisateur {user_id} supprimé"

    async def get_by_id(self, user_id: int) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user: User | None = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Utilisateur {user_id} introuvable"
            )
        return user

    async def get_by_email(self, email: str) -> User:
        if not email:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Adresse email invalide"
            )

        result = await self.db.execute(select(User).where(User.email == email))
        user: User | None = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Utilisateur introuvable à l'adresse : {email}"
            )
        return user

    async def get_all_users(self) -> List[User]:
        result = await self.db.execute(select(User))
        users: List[User] = result.scalars().all()
        return users
