from typing import Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.file import File
from datetime import datetime


class FileDAO:

    @staticmethod
    async def add_file(db: AsyncSession, file: File):
        """
        Ajoute un fichier ou un dossier en base.
        """
        db.add(file)
        await db.flush()

    @staticmethod
    async def commit(db: AsyncSession):
        await db.commit()

    @staticmethod
    async def list_children(
        db: AsyncSession,
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

        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def list_ch(db: AsyncSession, user_id: int, role_id: int, parent_id: str | None = None):
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

        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_file(db: AsyncSession, file_id: str):
        """
        Récupère un fichier ou dossier actif par son ID.
        """
        stmt = select(File).where(File.id == file_id)
        result = await db.execute(stmt)
        file = result.scalar_one_or_none()
        if not file:
            raise Exception("Fichier ou dossier introuvable")
        return file

    @staticmethod
    async def soft_delete(db: AsyncSession, file: File):
        """
        Supprime de manière soft un fichier ou dossier (status='deleted').
        """
        file.status = "deleted"
        file.updated_at = datetime.now()
        await db.flush()

    @staticmethod
    async def file_reactivate(db: AsyncSession, file: File):
        """
        Réactive un fichier ou dossier marqué comme supprimé (status='deleted').
        """
        file.status = "active"
        file.updated_at = datetime.now()
        await db.flush()

    @staticmethod
    async def hard_delete(db: AsyncSession, file: File):
        """
        Supprime définitivement un fichier ou dossier de la base.
        """
        await db.delete(file)
        await db.flush()

    @staticmethod
    async def rename(db: AsyncSession, file: File, new_name: str):
        file.logical_name = new_name
        file.updated_at = datetime.now()
        await db.flush()

    @staticmethod
    async def get_deleted_files(db: AsyncSession):
        """
        Récupère tous les fichiers marqués 'deleted'.
        """
        stmt = select(File).where(File.status == "deleted", File.is_directory == False)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_file_by_hash(db: AsyncSession, file_hash: str) -> Optional[File]:
        """
        Récupère un fichier par son hash (physique).
        Retourne None si aucun fichier trouvé.
        """
        stmt = select(File).where(File.hash == file_hash)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_active_file_by_hash_and_name(
        db: AsyncSession,
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
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_active_file_by_parent_and_name(
        db: AsyncSession,
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

        result = await db.execute(stmt)
        return result.scalars().first()
