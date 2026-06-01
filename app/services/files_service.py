from http import HTTPStatus
import os
from pathlib import Path
import shutil
import uuid
import hashlib
from datetime import datetime, timezone
from fastapi import UploadFile, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from app.dao.file_dao import FileDAO
from app.schemas.file_schema import FileModel, FileType, FolderModel
from app.models.file import File
from app.core.config import get_settings, Settings
from app.schemas.user_schema import UserOut
from app.services.ws_service import SocketIOService
from app.utils.file_utils import detect_mimetype, match_file_type


class FileService:
    def __init__(self, file_dao: FileDAO, socket: SocketIOService):
        self.file_dao = file_dao
        self.ws = socket
        self.config: Settings = get_settings()

        self.storage_root = Path(self.config.UPLOAD_DIR)
        self.trash_root = Path(self.config.TRASH_DIR)

        for path in (self.storage_root, self.trash_root):
            path.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    async def get_user_workspace_id(self, user_id: int) -> str:
        return await self.file_dao.get_storage_bucket_by_user_id(user_id)

    async def compute_physical_path(self, file: File) -> Path:
        parts = await self.file_dao.get_full_path_parts(file.id)
        return self.storage_root / file.storage_bucket / Path(*parts)

    async def compute_trash_path(self, file: File) -> Path:
        physical = await self.compute_physical_path(file)
        return self.trash_root / physical.relative_to(self.storage_root)

    async def move_files_to_trash(self, files: list[File]):
        for file in files:
            try:
                physical = await self.compute_physical_path(file)
                trash_path = await self.compute_trash_path(file)

                trash_path.parent.mkdir(parents=True, exist_ok=True)

                await self.safe_move(physical, trash_path)

            except Exception as e:
                raise HTTPException(500, e)

    async def file_exists_on_disk(self, file: File) -> bool:
        path = await self.compute_physical_path(file)
        if not path.exists():
            await self.file_dao.mark_file_missing(file)
            await self.file_dao.commit()
            return False
        return True

    async def safe_move(self, src: Path, dst: Path):
        dst.parent.mkdir(parents=True, exist_ok=True)
        await run_in_threadpool(lambda: shutil.move(str(src), str(dst)))

    async def safe_unlink(self, path: Path):
        if path.exists():
            await run_in_threadpool(lambda: path.unlink())

    async def get_file_by_id(self, file_id: str) -> File:
        """
        Récupère le fichier par son ID depuis la DB.
        """
        file = await self.file_dao.get_file(file_id)
        if not file:
            raise HTTPException(404, "Fichier introuvable")
        return file

    # ------------------------------------------------------------------
    # Upload File
    # ------------------------------------------------------------------

    async def save_file(
        self, file: UploadFile, user_id: int, role_id: int, parent_id: uuid.UUID | None = None
    ) -> FileModel:

        temp_path = self.storage_root / f".tmp_{uuid.uuid4()}"
        await run_in_threadpool(lambda: temp_path.parent.mkdir(parents=True, exist_ok=True))

        try:
            await run_in_threadpool(lambda: shutil.copyfileobj(file.file, temp_path.open("wb")))

            existing = await self.file_dao.get_active_file_by_parent_and_name(
                file.filename, user_id, role_id, parent_id
            )
            if existing:
                raise HTTPException(HTTPStatus.CONFLICT, f"Fichier '{file.filename}' existe déjà")

            storage_bucket = hashlib.sha1(str(user_id).encode()).hexdigest()[:8]

            ext = os.path.splitext(file.filename)[1].lower()

            db_file = File(
                id=uuid.uuid4(),
                user_id=user_id,
                parent_id=parent_id,
                logical_name=file.filename,
                is_directory=False,
                mime_type=(
                    "application/las"
                    if ext == ".las"
                    else "application/model" if ext == ".model" else file.content_type
                ),
                size_bytes=temp_path.stat().st_size,
                status="active",
                storage_bucket=storage_bucket,
            )

            await self.file_dao.add_file(db_file, user_id)
            await self.file_dao.flush()

            physical_path = await self.compute_physical_path(db_file)
            await self.safe_move(temp_path, physical_path)

            await self.file_dao.commit()

            return FileModel(
                id=str(db_file.id),
                name=db_file.logical_name,
                created_at=db_file.created_at,
                modified_at=db_file.updated_at,
                size_bytes=db_file.size_bytes,
                mimeType=db_file.mime_type,
                user_id=db_file.user_id,
            )

        except Exception:
            await self.file_dao.rollback()
            await self.safe_unlink(temp_path)
            raise

    # ------------------------------------------------------------------
    # Existing File
    # ------------------------------------------------------------------

    async def save_ml_result(
        self,
        paths: dict[str, Path],
        user_id: int,
        role_id: int,
        parent_id: uuid.UUID | str | None = None,
        ml_type: str = "train",
    ):

        # Crée un dossier par défaut si parent_id == 'root'
        if parent_id == "root":
            parent_dir = await self.create_directory(
                user_id, role_id, f"{ml_type}_{datetime.now().strftime('%y%m%d_%H%M')}"
            )
            parent_id = parent_dir.id
            physical_folder = await self.compute_physical_path(parent_dir)
            physical_folder.mkdir(parents=True, exist_ok=True)
        else:
            physical_folder = None

        saved_files = []

        try:
            for path in paths.values():
                destination = physical_folder / path.name if physical_folder else path

                existing = await self.file_dao.get_active_file_by_parent_and_name(
                    path.name, user_id, role_id, parent_id
                )
                if existing:
                    raise HTTPException(HTTPStatus.CONFLICT, f"Fichier '{path.name}' existe déjà")

                storage_bucket = hashlib.sha1(str(user_id).encode()).hexdigest()[:8]

                db_file = File(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    parent_id=parent_id,
                    logical_name=path.name,
                    is_directory=False,
                    mime_type=detect_mimetype(path),
                    size_bytes=path.stat().st_size,
                    status="active",
                    storage_bucket=storage_bucket,
                )

                if physical_folder:
                    await run_in_threadpool(lambda: shutil.move(str(path), str(destination)))

                await self.file_dao.add_file(db_file, user_id)
                saved_files.append((db_file, destination))

            await self.file_dao.commit()

        except Exception:
            await self.file_dao.rollback()
            # suppression physique des fichiers déplacés
            for _, dest in saved_files:
                try:
                    if dest.exists():
                        await run_in_threadpool(dest.unlink)
                except Exception:
                    pass
            raise

        result = {
            "saved_files": [str(f.logical_name) for f, _ in saved_files],
            "parent_id": str(parent_id),
            "path": str(physical_folder) if physical_folder else None,
        }

        return result

    # ------------------------------------------------------------------
    # Create directory
    # ------------------------------------------------------------------

    async def create_directory(
        self, user_id: int, role_id: int, name: str, parent_id: uuid.UUID | None = None
    ) -> File:
        existing = await self.file_dao.get_active_file_by_parent_and_name(
            name, user_id, role_id, parent_id
        )
        if existing:
            raise HTTPException(HTTPStatus.CONFLICT, "Dossier déjà existant")

        storage_bucket = hashlib.sha1(str(user_id).encode()).hexdigest()[:8]
        folder = File(
            id=uuid.uuid4(),
            user_id=user_id,
            parent_id=parent_id,
            logical_name=name,
            is_directory=True,
            status="active",
            storage_bucket=storage_bucket,
        )

        await self.file_dao.add_file(folder, user_id)
        await self.file_dao.commit()
        return folder

    # ------------------------------------------------------------------
    # List (DOSSIERS ET FICHIERS)
    # ------------------------------------------------------------------

    async def list_directory(
        self,
        user_id: int,
        role_id: int,
        parent_id: uuid.UUID | None = None,
        depth: int = 0,
        file_type: FileType = "all",
    ) -> FolderModel:

        entries = await self.file_dao.list_children(user_id, role_id, parent_id)

        folder = FolderModel(
            id=str(parent_id) if parent_id else "root",
            name="home",
            depth=depth,
            created_at=datetime.now(timezone.utc),
            modified_at=datetime.now(timezone.utc),
            children=[],
            size_bytes=0,
            user_id=user_id if parent_id is None else None,
        )

        for entry in entries:
            if not entry.is_directory:
                if not await self.file_exists_on_disk(entry):
                    continue

                if not match_file_type(entry, file_type):
                    continue

            if entry.is_directory:
                subfolder = await self.list_directory(
                    user_id, role_id, entry.id, depth + 1, file_type=file_type
                )
                subfolder.name = entry.logical_name
                subfolder.user_id = entry.user_id
                subfolder.created_at = entry.created_at
                subfolder.modified_at = entry.updated_at
                folder.children.append(subfolder)
                folder.size_bytes += subfolder.size_bytes
            else:
                folder.children.append(
                    FileModel(
                        id=str(entry.id),
                        name=entry.logical_name,
                        created_at=entry.created_at,
                        modified_at=entry.updated_at,
                        size_bytes=entry.size_bytes,
                        mimeType=entry.mime_type,
                        user_id=entry.user_id,
                    )
                )
                folder.size_bytes += entry.size_bytes or 0

        return folder

    # ------------------------------------------------------------------
    # Soft delete
    # ------------------------------------------------------------------

    async def delete_path(
        self, user_id: int, role_id: int, item_id: uuid.UUID, auto_commit: bool = True
    ) -> str:
        root = await self.file_dao.get_file(item_id)
        if not root:
            raise HTTPException(HTTPStatus.NOT_FOUND, "Objet introuvable")

        stack = [root]
        nodes: list[File] = []

        while stack:
            current = stack.pop()
            nodes.append(current)
            if current.is_directory:
                stack.extend(await self.file_dao.list_children(user_id, role_id, current.id))

        physical_root = await self.compute_physical_path(root)
        trash_root = await self.compute_trash_path(root)

        try:
            if physical_root.exists():
                await self.safe_move(physical_root, trash_root)

            for node in nodes:
                await self.file_dao.soft_delete(node, user_id)

            if auto_commit:
                await self.file_dao.commit()
            return "Objet supprimé avec succès"

        except Exception:
            if auto_commit:
                await self.file_dao.rollback()
            raise

    async def delete_user_workspace(self, user: UserOut, auto_commit: bool = True) -> list[File]:
        workspace_id = await self.get_user_workspace_id(user.id)
        if not workspace_id:
            return []

        files = await self.file_dao.get_user_workspace_files(workspace_id)
        if not files:
            return []

        # DB soft delete
        for file in files:
            await self.file_dao.soft_delete_workspace_files(user.id)

        if auto_commit:
            await self.file_dao.commit()

        return files

    # ------------------------------------------------------------------
    # Reactivate
    # ------------------------------------------------------------------

    async def reactivate_file(self, file_id: uuid.UUID) -> str:
        file = await self.file_dao.get_file(file_id)
        if not file or file.status != "deleted":
            raise HTTPException(HTTPStatus.BAD_REQUEST, "Non réactivable")

        original = await self.compute_physical_path(file)
        trash = await self.compute_trash_path(file)

        if not trash.exists():
            await self.file_dao.mark_file_missing(file)
            await self.file_dao.commit()
            raise HTTPException(HTTPStatus.CONFLICT, "Fichier manquant")

        try:
            await self.safe_move(trash, original)
            await self.file_dao.reactivate(file)
            await self.file_dao.commit()
            return "Fichier réactivé"

        except Exception:
            await self.file_dao.rollback()
            raise

    # ------------------------------------------------------------------
    # Rename
    # ------------------------------------------------------------------

    async def rename_path(
        self, item_id: uuid.UUID, user_id: int, role_id: int, new_name: str
    ) -> str:
        file = await self.file_dao.get_file(item_id)
        if not file:
            raise HTTPException(HTTPStatus.NOT_FOUND)

        existing = await self.file_dao.get_active_file_by_parent_and_name(
            new_name, user_id, role_id, file.parent_id
        )
        if existing and existing.id != file.id:
            raise HTTPException(HTTPStatus.CONFLICT, "Nom déjà utilisé")

        old_path = await self.compute_physical_path(file)

        try:
            await self.file_dao.rename(file, new_name)
            await self.file_dao.flush()

            new_path = await self.compute_physical_path(file)
            if old_path.exists():
                await self.safe_move(old_path, new_path)

            await self.file_dao.commit()
            return "Objet renommé"

        except Exception:
            await self.file_dao.rollback()
            raise

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    async def cleanup_deleted_files(self):
        files = await self.file_dao.get_deleted_files()

        for f in files:
            trash_path = await self.compute_trash_path(f)
            await self.safe_unlink(trash_path)
            await self.file_dao.hard_delete(f)

        await self.file_dao.commit()

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    async def download_file(self, item_id: uuid.UUID) -> FileResponse:
        file = await self.file_dao.get_file(item_id)
        if not file or file.status != "active":
            raise HTTPException(HTTPStatus.NOT_FOUND, "Fichier introuvable")
        if file.is_directory:
            raise HTTPException(HTTPStatus.BAD_REQUEST, "Dossier non téléchargeable")
        if not await self.file_exists_on_disk(file):
            raise HTTPException(HTTPStatus.GONE, "Fichier manquant sur le disque")
        physical_path = await self.compute_physical_path(file)
        response = FileResponse(
            path=physical_path,
            filename=file.logical_name,
            media_type=file.mime_type or "application/octet-stream",
        )
        response.headers["Access-Control-Expose-Headers"] = "Content-Disposition"
        return response
