from http import HTTPStatus
from pathlib import Path
import shutil
import uuid
import hashlib
from datetime import datetime
from fastapi import UploadFile, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.file_dao import FileDAO
from app.schemas.file_schema import FileModel, FolderModel
from app.services.interfaces.files_interface import IFileService
from app.services.interfaces.user_interface import IUserService
from app.models.file import File
from app.core.config import get_settings, Settings
import functools


class FileService(IFileService):
    """
    Service de gestion des fichiers
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
    async def compute_physical_path_async(self, db: AsyncSession, file: File, storage_root: Path) -> Path:
        """
        Retourne le chemin physique complet du fichier ou dossier, basé sur storage_bucket
        et arborescence logique. Fonctionne entièrement en async, sans lazy load sync.
        """
        parts = [file.logical_name]
        parent_id = file.parent_id

        while parent_id:
            stmt = select(File.logical_name, File.parent_id).where(File.id == parent_id)
            result = await db.execute(stmt)
            parent_record = result.first()
            if not parent_record:
                break
            parent_name, parent_id = parent_record
            parts.append(parent_name)

        parts.reverse()
        return storage_root / file.storage_bucket / Path(*parts)

    # ------------------------
    # Upload / création fichier
    # ------------------------
    async def save_file(
        self,
        file: UploadFile,
        user_id: int,
        role_id: int,
        db: AsyncSession,
        parent_id: uuid.UUID | None = None,
    ) -> FileModel:

        temp_path = self.storage_root / f"tmp_{uuid.uuid4()}"
        await run_in_threadpool(lambda: temp_path.parent.mkdir(parents=True, exist_ok=True))

        def write_temp_file():
            with temp_path.open("wb") as f:
                shutil.copyfileobj(file.file, f)

        await run_in_threadpool(write_temp_file)

        parent_uuid = None if parent_id in [None, "root"] else uuid.UUID(str(parent_id))

        existing_active = await FileDAO.get_active_file_by_parent_and_name(db, file.filename, user_id, role_id, parent_uuid)
        if existing_active:
            print(existing_active.storage_bucket)
            await run_in_threadpool(lambda: temp_path.unlink())
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail=f"Fichier '{file.filename}' existe déjà dans ce dossier"
            )

        storage_bucket = hashlib.sha1(str(user_id).encode()).hexdigest()[:8]
        db_file = File(
            id=uuid.uuid4(),
            user_id=user_id,
            parent_id=parent_uuid,
            logical_name=file.filename,
            is_directory=False,
            mime_type=file.content_type,
            size_bytes=await run_in_threadpool(lambda: temp_path.stat().st_size),
            status="active",
            storage_bucket=storage_bucket
        )

        await FileDAO.add_file(db, db_file)
        await FileDAO.commit(db)

        physical_path = await self.compute_physical_path_async(db, db_file, self.storage_root)
        await run_in_threadpool(lambda: physical_path.parent.mkdir(parents=True, exist_ok=True))
        await run_in_threadpool(lambda: shutil.move(str(temp_path), physical_path))

        return FileModel(
            id=str(db_file.id),
            name=db_file.logical_name,
            saved_as=db_file.logical_name,
            created_at=db_file.created_at,
            modified_at=db_file.updated_at,
            size_bytes=db_file.size_bytes,
            mimeType=db_file.mime_type,
            user_id=db_file.user_id
        )

    # ------------------------
    # Dossier
    # ------------------------

    async def create_directory(self, user_id: int, role_id: int, name: str, db: AsyncSession,
                               parent_id: uuid.UUID | None = None) -> str:
        # Vérification unicité
        existing_active = await FileDAO.get_active_file_by_parent_and_name(
            db, name, user_id, role_id, parent_id
        )
        if existing_active:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail=f"Dossier '{name}' existe déjà dans ce dossier"
            )

        storage_bucket = hashlib.sha1(str(user_id).encode()).hexdigest()[:8]
        folder = File(
            id=uuid.uuid4(),
            user_id=user_id,
            parent_id=parent_id,
            logical_name=name,
            is_directory=True,
            status="active",
            storage_bucket=storage_bucket
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
            name=None,
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
                    saved_as=entry.logical_name,
                    created_at=entry.created_at,
                    modified_at=entry.updated_at,
                    size_bytes=entry.size_bytes,
                    mimeType=entry.mime_type,
                    user_id=entry.user_id
                )
                folder.children.append(file_model)
                folder.size_bytes += entry.size_bytes or 0

        if parent_id is not None and entries:
            folder.user_id = entries[0].user_id

        return folder

    # ------------------------
    # Suppression soft
    # ------------------------
    async def delete_path(self, user_id: int, role_id: int, item_id: uuid.UUID, db: AsyncSession) -> str:
        root = await FileDAO.get_file(db, item_id)
        if not root:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Fichier introuvable")

        stack = [root]
        seen_ids = set()  # éviter cycles

        while stack:
            current = stack.pop()
            if current.id in seen_ids:
                continue
            seen_ids.add(current.id)

            if current.is_directory:
                # ici il faut passer current.id, pas item_id
                children = await FileDAO.list_children(db, user_id, role_id, parent_id=current.id)
                stack.extend(children)
            else:
                physical_path = await self.compute_physical_path_async(db, current, self.storage_root)
                if physical_path.exists():
                    trash_path = self.trash_root / physical_path.relative_to(self.storage_root)
                    trash_path.parent.mkdir(parents=True, exist_ok=True)
                    await run_in_threadpool(lambda: shutil.move(str(physical_path), trash_path))


            current.status = "deleted"
            current.updated_at = datetime.now()
            await db.flush()

        await FileDAO.commit(db)
        return "Objet supprimé avec succès"

    # ------------------------
    # Réactivation → recovery
    # ------------------------

    async def reactivate_file(self, file_id: uuid.UUID, db: AsyncSession) -> str:
        file = await FileDAO.get_file(db, file_id)
        if file.status != "deleted":
            raise HTTPException(HTTPStatus.BAD_REQUEST, "Fichier déjà actif")

        trash_path = self.trash_root / await self.compute_physical_path_async(db, file, self.storage_root).relative_to(self.storage_root)
        recovery_path = self.recovery_root / await self.compute_physical_path_async(db, file, self.storage_root).relative_to(self.storage_root)
        recovery_path.parent.mkdir(parents=True, exist_ok=True)
        if trash_path.exists():
            shutil.move(str(trash_path), recovery_path)

        file.status = "active"
        file.updated_at = datetime.now()
        await FileDAO.commit(db)
        return "Fichier réactivé dans recovery"

    # ------------------------
    # Rename
    # ------------------------
    async def rename_path(self, item_id: uuid.UUID, user_id: int, role_id: int, new_name: str, db: AsyncSession) -> str:
        file = await FileDAO.get_file(db, item_id)

        # Vérification unicité 
        existing = await FileDAO.get_active_file_by_parent_and_name(db, new_name, user_id, role_id, file.parent_id)
        if existing and existing.id != file.id:
            raise HTTPException(HTTPStatus.CONFLICT, f"Un objet avec le nom '{new_name}' existe déjà")

        old_physical_path = await self.compute_physical_path_async(db, file, self.storage_root)
        file.logical_name = new_name
        file.updated_at = datetime.now()
        await db.flush()
        await FileDAO.commit(db)

        # Renommer physiquement
        new_physical_path = await self.compute_physical_path_async(db, file, self.storage_root)
        if old_physical_path.exists():
            new_physical_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(old_physical_path), new_physical_path)

        return "Objet renommé avec succès"

    # ------------------------
    # Cleanup hard delete
    # ------------------------
    async def cleanup_deleted_files(self, db: AsyncSession):
        files = await FileDAO.get_deleted_files(db)
        for f in files:
            physical_path = await self.compute_physical_path_async(db, f, self.storage_root)
            if physical_path.exists():
                physical_path.unlink()
            await FileDAO.hard_delete(db, f)

    # ------------------------
    # Download file
    # ------------------------
    async def download_file(self, item_id: uuid.UUID, db: AsyncSession) -> FileResponse:
        file = await FileDAO.get_file(db, item_id)
        if not file or file.status != "active":
            raise HTTPException(HTTPStatus.NOT_FOUND, "Fichier introuvable")
        if file.is_directory:
            raise HTTPException(HTTPStatus.BAD_REQUEST, "Les dossiers ne sont pas supportés ici")

        physical_path = await self.compute_physical_path_async(db, file, self.storage_root)
        if not physical_path.exists():
            raise HTTPException(HTTPStatus.NOT_FOUND, "Fichier physique introuvable")

        res = FileResponse(
            path=physical_path,
            filename=file.logical_name,
            media_type=file.mime_type or "application/octet-stream",
        )

        res.headers["Access-Control-Expose-Headers"] = "Content-Disposition"
        return res

    async def get_item_physical_path(self, item_id: uuid.UUID, db: AsyncSession) -> Path:
        file = await FileDAO.get_file(db, item_id)
        if not file or file.status != "active":
            raise HTTPException(HTTPStatus.NOT_FOUND, "Fichier introuvable")
        if file.is_directory:
            raise HTTPException(HTTPStatus.BAD_REQUEST, "Les dossiers n'ont pas de chemin physique")

        physical_path = await self.compute_physical_path_async(db, file, self.storage_root)
        if not physical_path.exists():
            raise HTTPException(HTTPStatus.NOT_FOUND, "Fichier physique introuvable")

        return physical_path
