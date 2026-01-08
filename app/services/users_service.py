from http import HTTPStatus
from fastapi import HTTPException
from app.core.dao_provider import DAOProvider
from app.dao.interfaces.i_user_dao import IUserDAO
from app.models.user import User
from app.schemas.role_schema import UserRole
from app.schemas.user_schema import UserBase, UserIn, UserOut, UserUpdate
from app.services.interfaces.files_interface import IFileService
from app.services.interfaces.user_interface import IUserService
from app.utils.auth_utils import hash_password, raise_auth_exception
from typing import List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

class UserService(IUserService):
    """
    Service de gestion des utilisateurs.
    """
    def __init__(self):
        self.userDAO: IUserDAO = DAOProvider.get_user_dao()

    # --- CREATE ---
    async def create_user(self, user_data: UserIn, db: AsyncSession) -> UserOut:
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
        created_user = await self.userDAO.create(user, db)

        return UserOut.model_validate(created_user)

    # --- READ ---
    async def get_user_by_id(self, user_id: int, db: AsyncSession) -> UserOut:
        """
        Récupère un utilisateur par son ID.
        """
        user = await self.userDAO.get_by_id(user_id, db)
        return UserOut.model_validate(user)

    async def get_all_users(self, db: AsyncSession) -> List[UserOut]:
        """
        Retourne la liste complète des utilisateurs.
        """
        users: List[User] = await self.userDAO.get_all_users(db)
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
        
        user = await self.userDAO.get_by_email(email, db)
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
        user = await self.userDAO.get_by_email(email, db)
        if not user:
            raise_auth_exception("Email ou mot de passe incorrect")
        return UserBase.model_validate(user)
    
    # --- UPDATE ---
    async def update_user_by_id(self, user_id: int, fields: UserUpdate, db: AsyncSession) -> UserOut:
        """
        Met à jour un utilisateur partiellement.
        """
        await self.userDAO.get_by_id(user_id, db)
        update_data = fields.model_dump(exclude_unset=True)

        if "password" in update_data and update_data["password"]:
            update_data["password"] = hash_password(update_data["password"])
        update_data["updated_at"] = datetime.now()

        updated_user = await self.userDAO.update(user_id, update_data, db)
        return UserOut.model_validate(updated_user)


    # --- DELETE ---
    async def delete_user_by_id(self, user_id: int, db: AsyncSession) -> str:
        """
        Supprime un utilisateur par ID de manière atomique.
        """
        try:
            user = await self.get_user_by_id(user_id, db)
            await self.userDAO.delete(user.id, db)
            await db.commit()
            return f"Utilisateur supprimé avec succès."

        except HTTPException:
            await db.rollback()
            raise

        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Erreur interne: {e}")
        
    async def user_is_admin(self, user_id: int, db: AsyncSession) -> bool:
        try:
            user = await self.get_user_by_id(user_id, db)
            return user.role_id == UserRole.admin
        except HTTPException:
            raise


        
        
