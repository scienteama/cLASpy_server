from pathlib import Path
import os
import shutil
from datetime import datetime
import uuid
from fastapi import HTTPException, UploadFile
from app.schemas.file_schema import FileModel, FolderModel
from app.utils import file_utils
from http import HTTPStatus


class FileService:
    """
    Service métier pour la gestion des fichiers et dossiers.
    """
    def __init__(self, upload_dir: Path | str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)

    async def save_file(self, file: UploadFile, sub_path: str | None = None) -> FileModel:
        """Sauvegarde un fichier sur disque et retourne ses métadonnées."""
        safe_sub_path = (sub_path or "").lstrip("/\\")
        target_dir = self.upload_dir / safe_sub_path

        resolved_target = target_dir.resolve()
        if not str(resolved_target).startswith(str(self.upload_dir.resolve())):
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Invalid target path (must be inside uploads/)")

        resolved_target.mkdir(parents=True, exist_ok=True)

        now = datetime.now()
        saved_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = resolved_target / saved_filename

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

    async def list_directory(self, path: str = ".") -> FolderModel:
        """Retourne récursivement la structure d'un dossier sous forme d'arborescence."""
        target_dir = (self.upload_dir / path).resolve()

        def build_folder(directory: Path) -> FolderModel:
            folder = FolderModel(
                id=file_utils.generate_id_from_path(directory),
                name=directory.name,
                children=[],
                created_at=datetime.fromtimestamp(directory.stat().st_ctime),
                modified_at=datetime.fromtimestamp(directory.stat().st_mtime),
            )

            entries = sorted(
                os.scandir(directory),
                key=lambda e: (e.is_dir(), e.name.lower())
            )

            existing_names = set()
            for entry in entries:
                entry_path = Path(entry.path)
                if entry.is_dir():
                    folder.children.append(build_folder(entry_path))
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

        return build_folder(target_dir)

    async def delete_path(self, item_id: str) -> str:
        """Supprime un fichier ou un dossier à partir de son ID."""
        path = await file_utils.find_path_by_id(item_id, self.upload_dir)
        if not path:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Aucun fichier ou dossier trouvé pour l'ID {item_id}"
            )
        try:
            if path.is_file():
                os.remove(path)
            else:
                shutil.rmtree(path)
            return f"L'objet a été supprimé avec succès"
        except PermissionError:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail=f"Permission refusée pour supprimer l'objet {item_id}"
            )
        except FileNotFoundError:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"L'objet {item_id} n'existe plus"
            )
        except Exception as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Une erreur est survenue lors de la suppression : {e}"
            )

    async def rename_path(self, item_id: str, new_name: str) -> str:
        """Renomme un fichier ou un dossier à partir de son ID."""
        path = await file_utils.find_path_by_id(item_id, self.upload_dir)
        if not path:
            # Si le fichier/dossier n'existe pas → HTTP 404
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Aucun fichier ou dossier trouvé pour l'ID {item_id}"
            )

        new_path = path.parent / new_name

        try:
            os.rename(path, new_path)
            return f"L'objet a été renommé avec succès"
        except FileExistsError:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail=f"Un fichier ou dossier portant le nom {new_name} existe déjà"
            )
        except PermissionError:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail=f"Permission refusée pour renommer l'objet {item_id}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Une erreur est survenue lors du renommage : {e}"
            )

    async def create_directory(self, name: str, sub_path: str) -> str:
        """Crée un dossier à l'emplacement spécifié."""
        safe_sub_path = (sub_path or "").lstrip("/\\")
        target_dir = self.upload_dir / safe_sub_path / name

        resolved_target = target_dir.resolve()
        if not str(resolved_target).startswith(str(self.upload_dir.resolve())):
            raise HTTPException(HTTPStatus.BAD_REQUEST, detail="Invalid target path")

        try:
            resolved_target.mkdir(parents=True, exist_ok=False)
            return f"Le dossier {name} a été créé avec succès"
        except FileExistsError:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail=f"Le dossier {name} existe déjà."
            )
        except Exception as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Une erreur est survenue lors de la création du dossier {name}: {e}"
            )
