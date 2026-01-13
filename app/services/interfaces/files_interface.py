from pathlib import Path
from typing import Protocol
import uuid
from fastapi import File, UploadFile
from fastapi.responses import FileResponse
from app.schemas.file_schema import FileModel, FolderModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user_schema import UserOut
from app.services.interfaces.user_interface import IUserService


class IFileService(Protocol):
    async def save_file(self, file: UploadFile, user_id: int, role_id: int, db: AsyncSession,
                        parent_id: uuid.UUID | None = None) -> FileModel:
        """Sauvegarde un fichier et retourne ses métadonnées."""
        ...

    async def compute_physical_path_async(db: AsyncSession, file: File, storage_root: Path) -> Path:
        """
        Retourne le chemin physique d'un fichier ou dossier.
        """
        ...

    async def list_directory(self, user_id: int, role_id: int, db: AsyncSession,
                             parent_id: uuid.UUID | None = None, depth: int = 0) -> FolderModel:
        """Retourne l'arborescence d'un dossier"""
        ...

    async def delete_path(self, user_id: int, role_id: int, item_id: uuid.UUID, db: AsyncSession) -> str:
        """Supprime un fichier ou un dossier par son ID."""
        ...

    async def rename_path(self, item_id: uuid.UUID, user_id: int, role_id: int, new_name: str, db: AsyncSession) -> str:
        """Renomme un fichier ou dossier par son ID."""
        ...

    async def create_directory(self, user_id: int, role_id: int, name: str, db: AsyncSession,
                               parent_id: uuid.UUID | None = None) -> str:
        """Crée un dossier dans le dossier parent spécifié."""
        ...

    async def download_file(self, item_id: uuid.UUID, db: AsyncSession) -> FileResponse:
        """
        Télécharge un fichier via son ID.
        """
        ...
