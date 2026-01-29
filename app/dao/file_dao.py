from typing import Optional
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.file import File


class FileDAO:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------
    # Base operations
    # ------------------------

    async def add_file(self, file: File):
        """Ajoute un fichier dans la session db."""
        self.db.add(file)
        await self.db.flush()

    async def commit(self):
        await self.db.commit()

    async def flush(self):
        await self.db.flush()

    async def rollback(self):
        await self.db.rollback()

    # ------------------------
    # Getters
    # ------------------------

    async def get_file(self, file_id: uuid.UUID) -> Optional[File]:
        stmt = select(File).where(File.id == file_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_children(
        self,
        user_id: int,
        role_id: int,
        parent_id: Optional[uuid.UUID] = None,
        include_deleted: bool = False
    ):
        """Liste les enfants d'un dossier selon l'user et le status."""
        stmt = select(File).where(File.parent_id == parent_id)
        if not include_deleted:
            stmt = stmt.where(File.status == "active")

        if role_id != 1:  # non-admin
            stmt = stmt.where(File.user_id == user_id)

        stmt = stmt.order_by(File.is_directory.desc(), File.logical_name)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_active_file_by_parent_and_name(
        self,
        logical_name: str,
        user_id: int,
        role_id: int,
        parent_id: Optional[uuid.UUID] = None
    ) -> Optional[File]:
        """Récupère un fichier actif par parent et nom."""
        stmt = select(File).where(
            File.logical_name == logical_name,
            File.status == "active",
            File.parent_id.is_(None) if parent_id is None else File.parent_id == parent_id
        )

        if role_id != 1:  # non-admin
            stmt = stmt.where(File.user_id == user_id)

        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_deleted_files(self):
        stmt = select(File).where(
            File.status == "deleted",
            File.is_directory == False
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    # ------------------------
    # Status transitions
    # ------------------------

    async def soft_delete(self, file: File):
        """Marque un fichier/dossier comme supprimé (soft delete)."""
        file.status = "deleted"
        file.updated_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def reactivate(self, file: File):
        """Réactive un fichier si status=deleted."""
        if file.status == "missing":
            raise Exception("Impossible de réactiver un fichier manquant")
        file.status = "active"
        file.updated_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def mark_file_missing(self, file: File):
        """Marque un fichier comme manquant sur le disque."""
        if file.status != "missing":
            file.status = "missing"
            file.updated_at = datetime.now(timezone.utc)
            await self.db.flush()

    async def hard_delete(self, file: File):
        """Supprime définitivement un fichier de la DB."""
        await self.db.delete(file)
        await self.db.flush()

    # ------------------------
    # Rename
    # ------------------------

    async def rename(self, file: File, new_name: str):
        file.logical_name = new_name
        file.updated_at = datetime.now(timezone.utc)
        await self.db.flush()

    # ------------------------
    # Path computation
    # ------------------------

    async def get_full_path_parts(self, file_id: uuid.UUID) -> list[str]:
        """Retourne la liste des noms parents jusqu'à la racine."""
        parts: list[str] = []
        current_id = file_id

        while current_id:
            stmt = select(File.logical_name, File.parent_id).where(File.id == current_id)
            result = await self.db.execute(stmt)
            record = result.first()
            if not record:
                break  # un parent a été supprimé

            name, current_id = record
            parts.append(name)

        parts.reverse()
        return parts


#    TABLE DE VÉRITÉ — COHÉRENCE DB / DISQUE
# ======================================
#
# DB STATUS | DISQUE (user) | DISQUE (trash) | ACTION AUTORISÉE | RÉSULTAT
# -----------------------------------------------------------------------
# absent    | absent          | absent         | rien             | OK
# absent    | présent         | -              | log / alerte     | ORPHELIN
# active    | présent         | absent         | usage normal     | OK
# active    | absent          | absent         | mark missing     | DB => missing
# active    | absent          | présent        | interdit         | alerte
# deleted   | présent         | absent         | interdit         | alerte
# deleted   | absent          | présent        | attente TTL      | OK
# deleted   | absent          | absent         | mark missing     | DB => missing
# missing   | absent          | absent         | cleanup          | hard delete DB
# missing   | présent         | -              | admin restore    | active
