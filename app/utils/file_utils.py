import mimetypes
import uuid
from fastapi.params import Path

def detect_mimetype(file_path: Path, content_type: str | None = None) -> str:
    """
    Détecte le mimetype d'un fichier. Si FastAPI fournit déjà un content_type, on l'utilise.
    Sinon, on essaye de deviner à partir du nom.
    """
    if content_type:
        return content_type

    # Détection classique via mimetypes
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type:
        return mime_type

    # Cas spécifique pour les fichiers .LAS
    if file_path.suffix.lower() == ".las":
        return "application/las"

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
