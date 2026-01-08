from pathlib import Path
from typing import Protocol, Optional
from fastapi import UploadFile
from app.models.user import User
from app.schemas.file_schema import FileModel, FolderModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user_schema import UserOut
from app.services.interfaces.user_interface import IUserService

class IFileService(Protocol):
    async def save_file(self, file: UploadFile, user_id: int, db: AsyncSession, sub_path: str | None = None) -> FileModel:
        """Sauvegarde un fichier et retourne ses métadonnées."""
        ...

    async def list_directory(self, user_id: int, role_id: int, db: AsyncSession, path: str = ".") -> FolderModel:
        """Retourne l'arborescence d'un dossier selon les droits de l'utilisateur."""
        ...

    async def delete_path(self, item_id: str) -> str:
        """Supprime un fichier ou un dossier par son ID."""
        ...

    async def delete_user_dir(self, user: UserOut) -> str:
        """Supprime un dossier utilisateur et son contenu."""
        ...

    async def rename_path(self, item_id: str, new_name: str) -> str:
        """Renomme un fichier ou dossier par son ID."""
        ...

    async def create_directory(self, user_id: int, name: str, db: AsyncSession,  sub_path: str | None = None) -> str:
        """Crée un dossier à l'emplacement spécifié."""
        ...

    async def _get_user_dir(self, user_id: int, db: AsyncSession, sub_path: str | None = None) -> Path:
        """
        Retourne le path du dossier de l'utilisateur
        Crée le dossier si nécessaire.
        """
        ...
