from pathlib import Path
from typing import Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.file import File
from datetime import datetime


class FileDAO:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_file(self, file: File):
        """
        Ajoute un fichier ou un dossier en base.
        """
        self.db.add(file)
        await self.db.flush()

    async def commit(self):
        await self.db.commit()

    async def flush(self):
        await self.db.flush()

    async def list_children(
        self,
        user_id: int,
        role_id: int,
        parent_id: uuid.UUID | None = None
    ):
        """
        Retourne tous les enfants (fichiers et dossiers) actifs d'un parent.
        Si l'utilisateur est admin (role_id == 1), retourne tous les fichiers du parent,
        sinon seulement ceux appartenant à user_id.
        """
        stmt = select(File).where(
            File.parent_id == parent_id,
            File.status == "active"
        )

        if role_id != 1:
            stmt = stmt.where(File.user_id == user_id)

        stmt = stmt.order_by(File.is_directory.desc(), File.logical_name)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def list_ch(self, user_id: int, role_id: int, parent_id: str | None = None):
        """
        Retourne tous les enfants (fichiers et dossiers) actifs d'un parent.
        Si l'utilisateur est admin (role_id == 1), retourne tous les fichiers du parent,
        sinon seulement ceux appartenant à user_id.
        """
        stmt = select(File).where(
            File.parent_id == parent_id,
            File.status == "active"
        )

        if role_id != 1:
            stmt = stmt.where(File.user_id == user_id)

        stmt = stmt.order_by(File.is_directory.desc(), File.logical_name)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_file(self, file_id: str):
        """
        Récupère un fichier ou dossier actif par son ID.
        """
        stmt = select(File).where(File.id == file_id)
        result = await self.db.execute(stmt)
        file = result.scalar_one_or_none()
        if not file:
            raise Exception("Fichier ou dossier introuvable")
        return file

    async def soft_delete(self, file: File):
        """
        Supprime de manière soft un fichier ou dossier (status='deleted').
        """
        file.status = "deleted"
        file.updated_at = datetime.now()
        await self.db.flush()

    async def file_reactivate(self, file: File):
        """
        Réactive un fichier ou dossier marqué comme supprimé (status='deleted').
        """
        file.status = "active"
        file.updated_at = datetime.now()
        await self.db.flush()

    async def hard_delete(self, file: File):
        """
        Supprime définitivement un fichier ou dossier de la base.
        """
        await self.db.delete(file)
        await self.db.flush()

    async def rename(self, file: File, new_name: str):
        file.logical_name = new_name
        file.updated_at = datetime.now()
        await self.db.flush()

    async def get_deleted_files(self):
        """
        Récupère tous les fichiers marqués 'deleted'.
        """
        stmt = select(File).where(File.status == "deleted", File.is_directory == False)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_file_by_hash(self, file_hash: str) -> Optional[File]:
        """
        Récupère un fichier par son hash (physique).
        Retourne None si aucun fichier trouvé.
        """
        stmt = select(File).where(File.hash == file_hash)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_file_by_hash_and_name(
        self,
        file_hash: str,
        logical_name: str,
        user_id: int,
        parent_id: uuid.UUID | None = None,
    ) -> Optional[File]:
        """
        Récupère un fichier actif par hash, nom logique, utilisateur et dossier parent.
        Retourne None si aucun fichier trouvé.
        """
        stmt = select(File).where(
            File.hash == file_hash,
            File.logical_name == logical_name,
            File.user_id == user_id,
            File.parent_id == parent_id,
            File.status == "active"
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_file_by_parent_and_name(
        self,
        logical_name: str,
        user_id: int,
        role_id: int,
        parent_id: Optional[uuid.UUID] = None
    ) -> Optional[File]:

        stmt = select(File).where(
            File.logical_name == logical_name,
            File.status == "active"
        )

        if parent_id is None:
            stmt = stmt.where(File.parent_id.is_(None))
        else:
            stmt = stmt.where(File.parent_id == parent_id)

        if role_id != 1:  # not admin
            stmt = stmt.where(File.user_id == user_id)

        result = await self.db.execute(stmt)
        return result.scalars().first()

    # async def compute_physical_path_async(self, file: File, storage_root: Path) -> Path:
    #     """
    #     Retourne le chemin physique complet du fichier ou dossier
    #     """
    #     parts = [file.logical_name]
    #     parent_id = file.parent_id

    #     while parent_id:
    #         stmt = select(File.logical_name, File.parent_id).where(File.id == parent_id)
    #         result = await self.db.execute(stmt)
    #         parent_record = result.first()
    #         if not parent_record:
    #             break
    #         parent_name, parent_id = parent_record
    #         parts.append(parent_name)

    #     parts.reverse()
    #     return storage_root / file.storage_bucket / Path(*parts)
    
    async def get_full_path_parts(self, file_id: int) -> list[str]:
        """
        Retourne la liste des noms logiques du fichier jusqu'à la racine.
        Exemple: ['grand_parent', 'parent', 'mon_fichier.txt']
        """
        parts = []

        current_id = file_id
        while current_id:
            stmt = select(File.logical_name, File.parent_id).where(File.id == current_id)
            result = await self.db.execute(stmt)
            record = result.first()
            if not record:
                break
            name, current_id = record
            parts.append(name)

        parts.reverse()
        return parts
