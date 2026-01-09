from pathlib import Path
import shutil
import uuid
import hashlib
from datetime import datetime
from fastapi import UploadFile, HTTPException
from http import HTTPStatus
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.file_dao import FileDAO
from app.schemas.file_schema import FileModel, FolderModel
from app.services.interfaces.files_interface import IFileService
from app.services.interfaces.user_interface import IUserService
from app.models.file import File
from app.core.config import get_settings, Settings


class FileService(IFileService):
    """
    Service de gestion des fichiers :
    - Stockage basé sur hash
    - Unicité sur (hash + name)
    - Soft delete déplace le fichier physique vers une corbeille
    - Réactivation manuelle déplace vers un dossier recovery
    """

    def __init__(self, user_service: IUserService):
        self.user_service = user_service
        self.config: Settings = get_settings()
        self.storage_root = Path(self.config.UPLOAD_DIR)
        self.trash_root = Path(self.config.TRASH_DIR)
        self.recovery_root = Path(self.config.RECOVERY_DIR)

        # Créer les dossiers si manquants
        for path in [self.storage_root, self.trash_root, self.recovery_root]:
            path.mkdir(parents=True, exist_ok=True)

    # ------------------------
    # Utils
    # ------------------------
    def _compute_physical_path(self, file_hash: str) -> Path:
        """Chemin physique basé sur le hash (2 niveaux de sharding)."""
        shard1 = file_hash[:2]
        shard2 = file_hash[2:4]
        return self.storage_root / shard1 / shard2 / file_hash

    @staticmethod
    def _compute_file_hash(path: Path) -> str:
        """Calcule le SHA256 du fichier."""
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    # ------------------------
    # Upload / création fichier
    # ------------------------
    async def save_file(
        self,
        file: UploadFile,
        user_id: int,
        db: AsyncSession,
        parent_id: uuid.UUID | None = None,
    ) -> FileModel:
        temp_path = self.storage_root / f"tmp_{uuid.uuid4()}"
        temp_path.parent.mkdir(parents=True, exist_ok=True)

        # Écriture temporaire
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        # Calcul du hash
        file_hash = self._compute_file_hash(temp_path)
        # Vérification existence selon hash + name
        return await self._handle_existing_file(
            db=db,
            file_hash=file_hash,
            temp_path=temp_path,
            logical_name=file.filename,
            user_id=user_id,
            parent_id=parent_id,
            mime_type=file.content_type
        )

    async def _handle_existing_file(
        self,
        db: AsyncSession,
        file_hash: str,
        temp_path: Path,
        logical_name: str,
        user_id: int,
        parent_id: uuid.UUID | None = None,
        mime_type: str = "",
    ) -> FileModel:
        """
        Unicité basée sur hash + name :
        - Même hash + même nom actif → conflit
        - Même hash + nom différent → nouvelle entrée
        - Fichiers deleted ignorés (physiquement en corbeille)
        """
        # Vérifier si fichier actif existe avec même hash + name

        existing_active = await FileDAO.get_active_file_by_hash_and_name(db, file_hash, logical_name, user_id, parent_id)

        if existing_active:
            if temp_path.exists():
                temp_path.unlink()
                raise HTTPException(
                    status_code=409,
                    detail="Fichier déjà existant dans ce dossier"
                )

        # Déplacement physique
        physical_path = self._compute_physical_path(file_hash)
        physical_path.parent.mkdir(parents=True, exist_ok=True)

        if not physical_path.exists() and temp_path.exists():
            shutil.move(str(temp_path), physical_path)
        elif temp_path.exists():
            temp_path.unlink()

        # Création entrée en base
        db_file = File(
            id=uuid.uuid4(),
            user_id=user_id,
            parent_id=parent_id,
            logical_name=logical_name,
            is_directory=False,
            hash=file_hash,
            mime_type=mime_type,
            size_bytes=physical_path.stat().st_size if physical_path.exists() else 0,
            status="active",
        )
        await FileDAO.add_file(db, db_file)
        await FileDAO.commit(db)

        return FileModel(
            id=str(db_file.id),
            name=db_file.logical_name,
            saved_as=db_file.hash,
            created_at=db_file.created_at,
            modified_at=db_file.updated_at,
            size_bytes=db_file.size_bytes,
            mimeType=db_file.mime_type,
            user_id=db_file.user_id
        )

    # ------------------------
    # Dossier
    # ------------------------
    async def create_directory(self, user_id: int, name: str, db: AsyncSession,
                               parent_id: uuid.UUID | None = None) -> str:
        print(parent_id)
        folder = File(
            id=uuid.uuid4(),
            user_id=user_id,
            parent_id=parent_id,
            logical_name=name,
            is_directory=True,
            status="active"
        )
        await FileDAO.add_file(db, folder)
        await FileDAO.commit(db)
        return f"Dossier '{name}' créé avec succès"

    async def list_directory(
        self,
        user_id: int,
        role_id: int,
        db: AsyncSession,
        parent_id: uuid.UUID | None = None,
        depth: int = 0
    ) -> FolderModel:

        entries = await FileDAO.list_children(db, user_id, role_id, parent_id)

        folder = FolderModel(
            id=str(parent_id) if parent_id else "root",
            name="/" if parent_id is None else "",
            depth=depth,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            children=[],
            size_bytes=0,
            user_id=user_id if parent_id is None else None
        )

        for entry in entries:
            if entry.is_directory:
                subfolder = await self.list_directory(
                    user_id=user_id,
                    role_id=role_id,
                    db=db,
                    parent_id=entry.id,
                    depth=depth + 1,
                )

                subfolder.user_id = entry.user_id
                subfolder.name = entry.logical_name
                folder.children.append(subfolder)
                folder.size_bytes += subfolder.size_bytes

            else:
                file_model = FileModel(
                    id=str(entry.id),
                    name=entry.logical_name,
                    saved_as=entry.hash,
                    created_at=entry.created_at,
                    modified_at=entry.updated_at,
                    size_bytes=entry.size_bytes,
                    mimeType=entry.mime_type,
                    user_id=entry.user_id
                )
                folder.children.append(file_model)
                folder.size_bytes += entry.size_bytes or 0

        if parent_id is not None:
            folder.user_id = (entries[0].user_id if entries else user_id)

        return folder

    # ------------------------
    # Suppression soft → corbeille (récursive)
    # ------------------------

    async def delete_path(self, item_id: uuid.UUID, db: AsyncSession) -> str:
        file = await FileDAO.get_file(db, item_id)

        async def _delete_recursive(f: File):
            if f.is_directory:
                # Lister les enfants (tous)
                children = await FileDAO.list_children(db, f.user_id, str(f.id))
                for child in children:
                    await _delete_recursive(child)
            else:
                # Déplacer le fichier vers la corbeille
                physical_path = self._compute_physical_path(f.hash)
                if physical_path.exists():
                    trash_path = self.trash_root / physical_path.name
                    trash_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(physical_path), trash_path)

            # Marquer comme supprimé
            f.status = "deleted"
            f.updated_at = datetime.now()
            await db.flush()

        await _delete_recursive(file)
        await FileDAO.commit(db)
        return "Objet supprimé avec succès"

    # ------------------------
    # Réactivation manuelle → recovery
    # ------------------------
    async def reactivate_file(self, file_id: uuid.UUID, db: AsyncSession) -> str:
        file = await FileDAO.get_file(db, file_id)
        if file.status != "deleted":
            raise HTTPException(HTTPStatus.BAD_REQUEST, "Fichier déjà actif")

        # Déplacer le fichier depuis corbeille vers recovery
        trash_path = self.trash_root / file.hash
        recovery_path = self.recovery_root / file.hash
        recovery_path.parent.mkdir(parents=True, exist_ok=True)
        if trash_path.exists():
            shutil.move(str(trash_path), recovery_path)

        file.status = "active"
        await FileDAO.commit(db)
        return "Fichier réactivé dans recovery"

    # ------------------------
    # Rename
    # ------------------------
    async def rename_path(self, item_id: uuid.UUID, new_name: str, db: AsyncSession) -> str:
        file = await FileDAO.get_file(db, item_id)
        await FileDAO.rename(db, file, new_name)
        await FileDAO.commit(db)
        return "Objet renommé avec succès"

    # ------------------------
    # Cleanup hard delete
    # ------------------------
    async def cleanup_deleted_files(self, db: AsyncSession):
        files = await FileDAO.get_deleted_files(db)
        for f in files:
            trash_path = self.trash_root / f.hash
            if trash_path.exists():
                trash_path.unlink()
            await FileDAO.hard_delete(db, f)

    # ------------------------
    # Download file
    # ------------------------
    async def download_file(self, item_id: uuid.UUID, db: AsyncSession) -> FileResponse:
        """
        Télécharge un fichier simple
        """
        file = await FileDAO.get_file(db, item_id)

        if not file or file.status != "active":
            raise HTTPException(HTTPStatus.NOT_FOUND, "Fichier introuvable")

        if file.is_directory:
            raise HTTPException(HTTPStatus.BAD_REQUEST, "Les dossiers ne sont pas supportés ici")

        physical_path = self._compute_physical_path(file.hash)

        if not physical_path.exists():
            raise HTTPException(HTTPStatus.NOT_FOUND, "Fichier physique introuvable")

        return FileResponse(
            path=physical_path,
            filename=file.logical_name,
            media_type=file.mime_type or "application/octet-stream",
        )
