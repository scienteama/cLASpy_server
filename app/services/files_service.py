from pathlib import Path
import os
import shutil
from datetime import datetime
import uuid
from fastapi import HTTPException, UploadFile
from app.core.config import Settings, get_settings
from app.models.user import User
from app.schemas.file_schema import FileModel, FolderModel
from app.schemas.role_schema import UserRole
from app.schemas.user_schema import UserOut
from app.services.interfaces.files_interface import IFileService
from app.services.interfaces.user_interface import IUserService
from app.utils import file_utils
from http import HTTPStatus
from sqlalchemy.ext.asyncio import AsyncSession

class FileService(IFileService):
    """
    Service métier pour la gestion des fichiers et dossiers.
    """
    def __init__(self, user_service: IUserService | None = None):
        self.user_service = user_service
        self.config: Settings = get_settings()
        self.upload_dir = Path(self.config.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)


    async def _get_user_dir(self, user_id: int, db: AsyncSession, sub_path: str | None = None) -> Path:
        user = await self.user_service.get_user_by_id(user_id, db)
        folder_name = f"{user.id}_{user.firstname[0].lower()}{user.lastname.lower()}"
        user_dir = (self.upload_dir / "users" / folder_name).resolve()
        user_dir.mkdir(parents=True, exist_ok=True)

        if sub_path:
            target_dir = (user_dir / sub_path.lstrip("/\\")).resolve()
        else:
            target_dir = user_dir


        if not target_dir.is_relative_to(user_dir):
            raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Accès interdit")

        return target_dir
    
    async def _get_base_dir(self) -> Path:
        base_dir = self.upload_dir.resolve()
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir

    async def save_file(self, file: UploadFile, user_id: int, db: AsyncSession, sub_path: str | None = None) -> FileModel:

        if await self.user_service.user_is_admin(user_id, db):
            target_dir = await self._get_base_dir()
            if sub_path and sub_path != '/':
                target_dir = target_dir / sub_path
        else:
            target_dir = await self._get_user_dir(user_id, db, sub_path)


        
        
        ##target_dir = await self._get_user_dir(user_id, db, sub_path)
        target_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now()
        saved_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = target_dir / saved_filename



        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return FileModel(
            id=file_utils.generate_id_from_path(file_path),
            name=file.filename,
            saved_as=saved_filename,
            created_at=now,
            modified_at=now,
            size_bytes=file_path.stat().st_size,
            mimeType=file_utils.detect_mimetype(file_path, file.content_type),
        )

    async def create_directory(self, user_id: int, name: str, db: AsyncSession,  sub_path: str | None = None) -> str:

        if await self.user_service.user_is_admin(user_id, db):
            target_dir = await self._get_base_dir()
            if sub_path and sub_path != '/':
                target_dir = target_dir / sub_path
        else:
            target_dir = await self._get_user_dir(user_id, db, sub_path)




        
        target_dir = target_dir / name


    
        try:
            target_dir.mkdir(parents=True, exist_ok=False)
            return f"Le dossier {name} a été créé avec succès"
        except FileExistsError:
            raise HTTPException(status_code=HTTPStatus.CONFLICT, detail=f"Le dossier {name} existe déjà.")
        except Exception as e:
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la création du dossier : {e}")

    async def list_directory(self, user_id: int, db: AsyncSession, path: str = ".") -> FolderModel:

        if await self.user_service.user_is_admin(user_id, db):
            target_dir = await self._get_base_dir()
        else:
            target_dir = await self._get_user_dir(user_id, db, path)

        def build_folder(directory: Path, depth: int = 0) -> FolderModel:
            """Construit récursivement la structure du dossier avec profondeur."""

            
            folder = FolderModel(
                id=file_utils.generate_id_from_path(directory),
                name=directory.name or "/",  # racine
                children=[],
                created_at=datetime.fromtimestamp(directory.stat().st_ctime),
                modified_at=datetime.fromtimestamp(directory.stat().st_mtime),
                depth=depth,
            )

            # Lister et trier le contenu
            entries = sorted(os.scandir(directory), key=lambda e: (not e.is_dir(), e.name.lower()))
            existing_names = set()

            for entry in entries:
                entry_path = Path(entry.path)
                if entry.is_dir():
                    # Appel récursif avec profondeur +1
                    folder.children.append(build_folder(entry_path, depth + 1))
                else:
                    true_name = file_utils.extract_true_name(entry.name)
                    true_name = file_utils.get_unique_display_name(true_name, existing_names)
                    existing_names.add(true_name)
                    folder.children.append(
                        FileModel(
                            id=file_utils.generate_id_from_path(entry_path),
                            name=true_name,
                            saved_as=entry.name,
                            created_at=datetime.fromtimestamp(entry_path.stat().st_ctime),
                            modified_at=datetime.fromtimestamp(entry_path.stat().st_mtime),
                            size_bytes=entry_path.stat().st_size,
                            mimeType=file_utils.detect_mimetype(entry_path),
                        )
                    )
            return folder

        return build_folder(target_dir, depth=0)

    async def delete_path(self, item_id: str) -> str:
        path = await file_utils.find_path_by_id(item_id, self.upload_dir)
        if not path:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"Aucun fichier ou dossier trouvé pour l'ID {item_id}")
        try:
            if path.is_file():
                os.remove(path)
            else:
                shutil.rmtree(path)
            return f"L'objet a été supprimé avec succès"
        except PermissionError:
            raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail=f"Permission refusée pour supprimer l'objet {item_id}")
        except FileNotFoundError:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"L'objet {item_id} n'existe plus")
        except Exception as e:
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la suppression : {e}")
        
    async def delete_user_dir(self, user: UserOut) -> str:
        folder = f"{user.id}_{user.firstname[0].lower()}{user.lastname.lower()}"
        user_dir = self.upload_dir / "users" / folder

        if not user_dir.exists():
             return f"Dossier utilisateur {user.id} introuvable"
        try:
            shutil.rmtree(user_dir)
            return f"Dossier de l'utilisateur supprimé avec succès"
        except PermissionError:
            raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail=f"Permission refusée pour supprimer le dossier de l'utilisateur {user.id}")
        except Exception as e:
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f"Erreur lors de la suppression du dossier : {e}")

    async def rename_path(self, item_id: str, new_name: str) -> str:
        path = await file_utils.find_path_by_id(item_id, self.upload_dir)
        if not path:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=f"Aucun fichier ou dossier trouvé pour l'ID {item_id}")
        new_path = path.parent / new_name
        try:
            os.rename(path, new_path)
            return f"L'objet a été renommé avec succès"
        except FileExistsError:
            raise HTTPException(status_code=HTTPStatus.CONFLICT, detail=f"Un fichier ou dossier portant le nom {new_name} existe déjà")
        except PermissionError:
            raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail=f"Permission refusée pour renommer l'objet {item_id}")
        except Exception as e:
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f"Erreur lors du renommage : {e}")
