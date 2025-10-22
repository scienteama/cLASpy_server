from pathlib import Path
import os
import shutil
from datetime import datetime
import hashlib
import mimetypes
import uuid
from fastapi import HTTPException, UploadFile
from app.schemas.file_schema import FileModel, FolderModel
from app.utils.file_utils import detect_mimetype, extract_true_name

class FileService:
    """
    Service métier pour la gestion des fichiers et dossiers.
    """
    
    def __init__(self, upload_dir: Path | str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)

    # --- UTILITAIRES ---

    def _generate_id_from_path(self, path: Path) -> str:
        """Génère un identifiant unique basé sur le chemin absolu."""
        return hashlib.sha1(str(path.resolve()).encode()).hexdigest()

    async def _find_path_by_id(self, item_id: str) -> Path | None:
        """Recherche un fichier ou dossier à partir de son identifiant."""
        for root, dirs, files in os.walk(self.upload_dir, topdown=False):
            root_path = Path(root)
            for file_name in files:
                file_path = root_path / file_name
                if self._generate_id_from_path(file_path) == item_id:
                    return file_path
            for dir_name in dirs:
                dir_path = root_path / dir_name
                if self._generate_id_from_path(dir_path) == item_id:
                    return dir_path
        return None

    # --- MÉTHODES ---

    async def save_file(self, file: UploadFile, sub_path: str | None = None) -> FileModel:
        """Sauvegarde un fichier sur disque et retourne ses métadonnées."""
        safe_sub_path = (sub_path or "").lstrip("/\\")
        target_dir = self.upload_dir / safe_sub_path

        resolved_target = target_dir.resolve()
        if not str(resolved_target).startswith(str(self.upload_dir.resolve())):
            raise HTTPException(status_code=400, detail="Invalid target path (must be inside uploads/)")

        resolved_target.mkdir(parents=True, exist_ok=True)

        now = datetime.now()
        saved_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = resolved_target / saved_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return FileModel(
            id=self._generate_id_from_path(file_path),
            name=file.filename,
            saved_as=saved_filename,
            created_at=now,
            modified_at=now,
            size_bytes=file_path.stat().st_size,
            mimeType=detect_mimetype(file_path, file.content_type),
        )

    async def list_directory(self, path: str = ".") -> FolderModel:
        """Retourne récursivement la structure d’un dossier sous forme d’arborescence."""
        target_dir = (self.upload_dir / path).resolve()

        def build_folder(directory: Path) -> FolderModel:
            folder = FolderModel(
                id=self._generate_id_from_path(directory),
                name=directory.name,
                children=[],
                created_at=datetime.fromtimestamp(directory.stat().st_ctime),
                modified_at=datetime.fromtimestamp(directory.stat().st_mtime),
            )

            entries = sorted(
                os.scandir(directory),
                key=lambda e: (e.is_dir(), e.name.lower())
            )

            for entry in entries:
                entry_path = Path(entry.path)
                if entry.is_dir():
                    folder.children.append(build_folder(entry_path))
                else:
                    true_name = extract_true_name(entry.name)
                    folder.children.append(
                        FileModel(
                            id=self._generate_id_from_path(entry_path),
                            name=true_name,
                            saved_as=entry.name,
                            created_at=datetime.fromtimestamp(entry_path.stat().st_ctime),
                            modified_at=datetime.fromtimestamp(entry_path.stat().st_mtime),
                            size_bytes=entry_path.stat().st_size,
                            mimeType=detect_mimetype(entry_path),
                        )
                    )

            return folder

        return build_folder(target_dir)

    async def delete_path(self, item_id: str) -> bool:
        """Supprime un fichier ou un dossier à partir de son ID."""
        path = await self._find_path_by_id(item_id)
        if not path:
            return False

        try:
            if path.is_file():
                os.remove(path)
            else:
                shutil.rmtree(path)
            return True
        except Exception as e:
            print(f"Erreur suppression {path}: {e}")
            return False

    async def rename_path(self, item_id: str, new_name: str) -> bool:
        """Renomme un fichier ou un dossier à partir de son ID."""
        path = await self._find_path_by_id(item_id)
        if not path:
            return False

        new_path = path.parent / new_name
        try:
            os.rename(path, new_path)
            return True
        except Exception as e:
            print(f"Erreur renommage {path} -> {new_name}: {e}")
            return False

    async def create_directory(self, name: str, sub_path: str) -> bool:
        """Crée un dossier à l’emplacement spécifié."""
        safe_sub_path = (sub_path or "").lstrip("/\\")
        target_dir = self.upload_dir / safe_sub_path / name

        print(f"Creating directory at: {target_dir}")

        resolved_target = target_dir.resolve()
        if not str(resolved_target).startswith(str(self.upload_dir.resolve())):
            raise HTTPException(status_code=400, detail="Invalid target path")

        try:
            resolved_target.mkdir(parents=True, exist_ok=False)
            return True
        except FileExistsError:
            print(f"Le dossier {resolved_target} existe déjà.")
            return False
        except Exception as e:
            print(f"Erreur création dossier {resolved_target}: {e}")
            return False
