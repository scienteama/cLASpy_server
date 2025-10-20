from pathlib import Path
import os
import shutil
from datetime import datetime
import hashlib
import mimetypes
import uuid
from fastapi import HTTPException, UploadFile
from app.schemas.file_schema import FileModel, FolderModel
from app.utils.file_utils import detect_mimetype


# --- Dossier de base ---
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# --- Utilitaires ---
def generate_id_from_path(path: Path) -> str:
    """
    Génère un identifiant basé sur le chemin absolu du fichier/dossier.
    """
    return hashlib.sha1(str(path.resolve()).encode()).hexdigest()


async def find_path_by_id(item_id: str) -> Path | None:
    """
    Recherche un fichier ou un dossier à partir de son ID (hash path).
    """
    for root, dirs, files in os.walk(UPLOAD_DIR, topdown=False):
        root_path = Path(root)

        # Fichiers
        for file_name in files:
            file_path = root_path / file_name
            if generate_id_from_path(file_path) == item_id:
                return file_path

        # Dossiers
        for dir_name in dirs:
            dir_path = root_path / dir_name
            if generate_id_from_path(dir_path) == item_id:
                return dir_path

    return None


# --- Sauvegarde de fichier ---
async def save_file(file: UploadFile, sub_path: str | None = None) -> FileModel:
    """
    Sauvegarde un fichier.

    :param file: Fichier envoyé par le client
    :param sub_path: Chemin relatif (ex: 'docs/2025/') — doit être enfant de UPLOAD_DIR
    :return: FileModel contenant les métadonnées
    """
    # Calcul du dossier cible
    safe_sub_path = (sub_path or "").lstrip("/\\")
    target_dir = UPLOAD_DIR / safe_sub_path

    print('sub_path:', sub_path)
    print('target_dir:', target_dir)

    # Sécurité : on résout le chemin et on vérifie qu'il est bien enfant de UPLOAD_DIR
    resolved_target = target_dir.resolve()
    if not str(resolved_target).startswith(str(UPLOAD_DIR.resolve())):
        raise HTTPException(status_code=400, detail="Invalid target path (must be inside uploads/)")

    # Création du dossier si nécessaire
    resolved_target.mkdir(parents=True, exist_ok=True)

    # Nom final du fichier
    now = datetime.now()
    saved_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = resolved_target / saved_filename

    # Sauvegarde sur disque
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Construction du modèle
    return FileModel(
        id=generate_id_from_path(file_path),
        name=file.filename,
        saved_as=saved_filename,
        created_at=now,
        modified_at=now,
        size_bytes=file_path.stat().st_size,
        mimeType=detect_mimetype(file_path, file.content_type)
    )


# --- Lecture récursive du dossier ---
async def list_directory(path: str = ".") -> FolderModel:
    """
    Construit récursivement la structure des dossiers et fichiers avec leur ID.
    """
    target_dir = (UPLOAD_DIR / path).resolve()

    def build_folder(directory: Path) -> FolderModel:
        folder = FolderModel(
            id=generate_id_from_path(directory),
            name=directory.name,
            children=[],
            created_at=datetime.fromtimestamp(directory.stat().st_ctime),
            modified_at=datetime.fromtimestamp(directory.stat().st_mtime))

        entries = sorted(
            os.scandir(directory),
            key=lambda e: (e.is_dir(), e.name.lower())  # trie par type puis par nom
        )

        for entry in entries:
            entry_path = Path(entry.path)

            if entry.is_dir():
                folder.children.append(build_folder(entry_path))
            else:
                mime_type, _ = mimetypes.guess_type(str(entry_path))
                splitName = entry.name.split("_", 1)
                trueName = splitName[1] if len(splitName) > 1 else entry.name
                folder.children.append(
                    FileModel(
                        id=generate_id_from_path(entry_path),
                        name=trueName,
                        saved_as=entry.name,
                        created_at=datetime.fromtimestamp(entry_path.stat().st_ctime),
                        modified_at=datetime.fromtimestamp(entry_path.stat().st_mtime),
                        size_bytes=entry_path.stat().st_size,
                        mimeType=detect_mimetype(entry_path)
                    )
                )

        return folder

    return build_folder(target_dir)



# --- Suppression fichier ou dossier ---
async def delete_path(item_id: str) -> bool:
    """
    Supprime un fichier ou un dossier en se basant sur son ID (hash path).
    """
    path = await find_path_by_id(item_id)
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


# --- Renommage fichier ou dossier ---
async def rename_path(item_id: str, new_name: str) -> bool:
    """
    Renomme un fichier ou un dossier grâce à son ID (hash path).
    """
    path = await find_path_by_id(item_id)
    if not path:
        return False

    new_path = path.parent / new_name
    try:
        os.rename(path, new_path)
        return True
    except Exception as e:
        print(f"Erreur renommage {path} -> {new_name}: {e}")
        return False
    
async def create_directory(name: str, subPath: str) -> bool:
    """
    Crée un nouveau dossier à l'emplacement spécifié.

    :param name: Nom du nouveau dossier
    :param subPath: Chemin relatif où créer le dossier (ex: 'docs/2025/')
    :return: Booléen indiquant le succès de l'opération
    """
    # Calcul du dossier cible
    safe_sub_path = (subPath or "").lstrip("/\\")
    target_dir = UPLOAD_DIR / safe_sub_path / name

    resolved_target = target_dir.resolve()
    if not str(resolved_target).startswith(str(UPLOAD_DIR.resolve())):
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
