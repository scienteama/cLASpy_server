import hashlib
import mimetypes
import os
import uuid
from pathlib import Path as PathLib

from app.models.file import File
from app.schemas.file_schema import FileType


def detect_mimetype(file_path: PathLib, content_type: str | None = None) -> str:
    """
    Détecte le mimetype d'un fichier.
    - Si FastAPI fournit déjà un content_type, on l'utilise.
    - Sinon, on essaye de deviner à partir du nom.
    """
    if content_type:
        return content_type

    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type:
        return mime_type

    # Cas spécifique pour les fichiers .LAS
    if file_path.suffix.lower() == ".las":
        return "application/las"

    elif file_path.suffix.lower() == ".model":
        return "application/model"

    # Valeur par défaut
    return "application/octet-stream"


def extract_true_name(saved_name: str) -> str:
    """
    Récupère le vrai nom d'un fichier.
    Si le fichier commence par un UUID suivi de '_', on supprime ce préfixe.
    Sinon, on renvoie le nom tel quel.
    """
    parts = saved_name.split("_", 1)
    try:
        uuid.UUID(parts[0])
        return parts[1]
    except (ValueError, IndexError):
        return saved_name


def get_unique_display_name(name: str, existing_names: set) -> str:
    """
    Génère un nom d'affichage unique pour un fichier en évitant les doublons.

    Lorsqu'un fichier avec le même nom existe déjà dans la liste `existing_names`,
    cette fonction ajoute un suffixe numérique entre parenthèses avant l'extension
    pour le rendre unique. Par exemple : "document.txt" → "document (1).txt".
    """
    base, ext = os.path.splitext(name)
    counter = 1
    new_name = name
    while new_name in existing_names:
        new_name = f"{base} ({counter}){ext}"
        counter += 1
    return new_name


def generate_id_from_path(path: PathLib) -> str:
    """Génère un identifiant unique basé sur le chemin absolu."""
    return hashlib.sha1(str(path.resolve()).encode()).hexdigest()


async def find_path_by_id(item_id: str, folder_path: PathLib) -> PathLib | None:
    """
    Recherche un fichier ou dossier à partir de son identifiant dans un répertoire donné.
    Parcours récursif en profondeur.
    """
    for root, dirs, files in os.walk(folder_path, topdown=False):
        root_path = PathLib(root)
        for file_name in files:
            file_path = root_path / file_name
            if generate_id_from_path(file_path) == item_id:
                return file_path
        for dir_name in dirs:
            dir_path = root_path / dir_name
            if generate_id_from_path(dir_path) == item_id:
                return dir_path
    return None


def compute_checksum(file_path: PathLib) -> str:
    """
    Calcule le checksum SHA-1 d'un fichier.
    """
    sha1 = hashlib.sha1()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha1.update(chunk)
    return sha1.hexdigest()


def find_duplicate_file(file_bytes: bytes, folder_path: PathLib) -> PathLib | None:
    """
    Vérifie si un fichier identique (même checksum SHA-1) existe déjà dans un dossier.

    Args:
        file_bytes: Contenu du fichier uploadé.
        folder_path: Dossier où rechercher les fichiers existants.

    Returns:
        Path du fichier existant identique, ou None si aucun doublon.
    """
    new_file_checksum = hashlib.sha1(file_bytes).hexdigest()

    for existing_file in folder_path.iterdir():
        if existing_file.is_file():
            existing_checksum = compute_checksum(existing_file)
            if existing_checksum == new_file_checksum:
                return existing_file

    return None

def match_file_type(entry: File, file_type: FileType) -> bool:
    if file_type == "all":
        return True
    if file_type == "model":
        return entry.logical_name.endswith(".model")
    if file_type == "las":
        return entry.logical_name.endswith(".las")
    return True
