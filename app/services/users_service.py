from http import HTTPStatus
from fastapi import Depends, HTTPException
from app.dao.user_dao import UserDAO
from app.models.user import User
from app.schemas.user_schema import UserBase, UserIn, UserOut, UserUpdate
from app.utils.auth_utils import hash_password, raise_auth_exception
from typing import Annotated, List, Type
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

class UserService:
    """
    Service de gestion des utilisateurs.
    """
    def __init__(self, user_dao_cls: Type[UserDAO]):
        self.user_dao_cls = user_dao_cls

    # --- CREATE ---
    async def create_user(self, user_data: UserIn, db: AsyncSession) -> UserOut:
        """
        Crée un nouvel utilisateur en hachant son mot de passe.
        """
        user_dao = self.user_dao_cls(db)
        hashed_password = hash_password(user_data.password)
        user = User(
            firstname=user_data.firstname,
            lastname=user_data.lastname,
            email=user_data.email,
            password=hashed_password,
            role_id=user_data.role_id,
            createdAt=datetime.now(),
            updatedAt=datetime.now(),
        )
        created_user = await user_dao.create(user)
        return UserOut.model_validate(created_user)

    # --- READ ---
    async def get_user_by_id(self, user_id: int, db: AsyncSession) -> UserOut:
        """
        Récupère un utilisateur par son ID.
        """
        user_dao = self.user_dao_cls(db)
        user = await user_dao.get_by_id(user_id)
        return UserOut.model_validate(user)

    async def get_all_users(self, db: AsyncSession) -> List[UserOut]:
        """
        Retourne la liste complète des utilisateurs.
        """
        user_dao = self.user_dao_cls(db)
        users: List[User] = await user_dao.get_all_users()
        return [UserOut.model_validate(u) for u in users]

    async def get_user_by_email(self, email: str, db: AsyncSession) -> UserOut:
        """
        Récupère un utilisateur par son email.
        """
        if not email:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Adresse email invalide."
            )
        
        user_dao = self.user_dao_cls(db)
        user = await user_dao.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Adresse email inconnue."
            )
        return UserOut.model_validate(user)
    
    async def get_full_user_by_email(self, email: str, db: AsyncSession) -> UserBase:
        """
        Récupère un utilisateur complet via son email.
        """
        user_dao = self.user_dao_cls(db)
        user = await user_dao.get_by_email(email)
        if not user:
            raise_auth_exception("Email ou mot de passe incorrect")
        return UserBase.model_validate(user)
    
    # --- UPDATE ---
    async def update_user_by_id(self, user_id: int, fields: UserUpdate, db: AsyncSession) -> UserOut:
        """
        Met à jour un utilisateur partiellement.
        """
        user_dao = self.user_dao_cls(db)
        await user_dao.get_by_id(user_id)
        update_data = fields.model_dump(exclude_unset=True)

        if "password" in update_data and update_data["password"]:
            update_data["password"] = hash_password(update_data["password"])
        update_data["updated_at"] = datetime.now()

        updated_user = await user_dao.update(user_id, update_data)
        return UserOut.model_validate(updated_user)


    # --- DELETE ---
    async def delete_user_by_id(self, user_id: int, db: AsyncSession) -> str:
        """
        Supprime un utilisateur par ID.
        """
        user_dao = self.user_dao_cls(db)
        result = await user_dao.delete(user_id)
        return result
