from http import HTTPStatus
from fastapi import HTTPException
from app.dao.user_dao import UserDAO
from app.models.user import User
from app.schemas.role_schema import UserRole
from app.schemas.user_schema import UserBase, UserIn, UserOut, UserUpdate
from app.utils.auth_utils import hash_password, raise_auth_exception
from typing import List
from datetime import datetime


class UserService:
    """
    Service de gestion des utilisateurs.
    """

    def __init__(self, user_dao: UserDAO):
        self.userDAO = user_dao

    # --- CREATE ---
    async def create_user(self, user_data: UserIn) -> UserOut:
        """
        Crée un nouvel utilisateur en hachant son mot de passe.
        """
        hashed_password = hash_password(user_data.password)
        user = User(
            firstname=user_data.firstname,
            lastname=user_data.lastname,
            email=user_data.email,
            password=hashed_password,
            role_id=user_data.role_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        created_user = await self.userDAO.create(user)

        return UserOut.model_validate(created_user)

    # --- READ ---
    async def get_user_by_id(self, user_id: int) -> UserOut:
        """
        Récupère un utilisateur par son ID.
        """
        user = await self.userDAO.get_by_id(user_id)
        return UserOut.model_validate(user)

    async def get_all_users(self) -> List[UserOut]:
        """
        Retourne la liste complète des utilisateurs.
        """
        users: List[User] = await self.userDAO.get_all_users()
        return [UserOut.model_validate(u) for u in users]

    async def get_user_by_email(self, email: str) -> UserOut:
        """
        Récupère un utilisateur par son email.
        """
        if not email:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Adresse email invalide."
            )

        user = await self.userDAO.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Adresse email inconnue."
            )
        return UserOut.model_validate(user)

    async def get_full_user_by_email(self, email: str) -> UserBase:
        """
        Récupère un utilisateur complet via son email.
        """
        user = await self.userDAO.get_by_email(email)
        if not user:
            raise_auth_exception("Email ou mot de passe incorrect")
        return UserBase.model_validate(user)

    # --- UPDATE ---
    async def update_user_by_id(self, user_id: int, fields: UserUpdate) -> UserOut:
        """
        Met à jour un utilisateur partiellement.
        """
        await self.userDAO.get_by_id(user_id)
        update_data = fields.model_dump(exclude_unset=True)

        if "password" in update_data and update_data["password"]:
            update_data["password"] = hash_password(update_data["password"])
        update_data["updated_at"] = datetime.now()

        updated_user = await self.userDAO.update(user_id, update_data)
        return UserOut.model_validate(updated_user)

    # --- DELETE ---

    async def delete_user_by_id(self, user_id: int) -> str:
        """
        Supprime un utilisateur par ID de manière atomique.
        """
        user = await self.get_user_by_id(user_id)
        await self.userDAO.delete(user.id)
        return f"Utilisateur supprimé avec succès."

    async def user_is_admin(self, user_id: int) -> bool:
        try:
            user = await self.get_user_by_id(user_id)
            return user.role_id == UserRole.admin
        except HTTPException:
            raise
