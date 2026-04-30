from http import HTTPStatus
from fastapi import HTTPException
from app.dao.user_dao import UserDAO
from app.models.user import User, UserStorage
from app.schemas.role_schema import UserRole
from app.schemas.user_schema import UserBase, UserIn, UserOut, UserStorageDTO, UserUpdate
from app.services.files_service import FileService
from app.utils.auth_utils import hash_password, raise_auth_exception
from typing import List
from datetime import datetime, timezone


class UserService:
    """
    Service de gestion des utilisateurs.
    """

    def __init__(self, user_dao: UserDAO, file_service: FileService):
        self.userDAO = user_dao
        self.file_service = file_service

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
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        user.storage = UserStorage(storage_used_bytes=0)
        created_user = await self.userDAO.create(user)

        return UserOut.model_validate(created_user)

    # --- READ ---
    async def get_user_by_id(self, user_id: int) -> UserOut:
        user = await self.userDAO.get_by_id(user_id)

        storage = await self.userDAO.get_user_storage_by_user_id(user_id)
        u_storage = UserStorageDTO.model_validate(storage) if storage else None

        return UserOut(
            id=user.id,
            firstname=user.firstname,
            lastname=user.lastname,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            role_id=user.role_id,
            storage=u_storage,
        )

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
                status_code=HTTPStatus.BAD_REQUEST, detail="Adresse email invalide."
            )

        user = await self.userDAO.get_by_email(email)
        if not user:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Adresse email inconnue.")
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
        update_data["updated_at"] = datetime.now(timezone.utc)

        updated_user = await self.userDAO.update(user_id, update_data)
        return UserOut.model_validate(updated_user)

    # --- DELETE ---

    async def delete_user_by_id(self, user_id: int) -> str:
        user = await self.get_user_by_id(user_id)

        try:
            # soft delete
            files = await self.file_service.delete_user_workspace(user, auto_commit=False)

            # delete user
            await self.userDAO.delete(user.id)

            # commit DB
            await self.userDAO.db.commit()

        except Exception:
            await self.userDAO.db.rollback()
            raise

        # move to trash
        await self.file_service.move_files_to_trash(files)

        return "Utilisateur supprimé avec succès"

    async def user_is_admin(self, user_id: int) -> bool:
        try:
            user = await self.get_user_by_id(user_id)
            return user.role_id == UserRole.admin
        except HTTPException:
            raise
