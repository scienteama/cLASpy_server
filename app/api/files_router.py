from fastapi.params import Form
from app.schemas.file_schema import FileModel, FolderModel
from app.core.service_provider import ServiceProvider
from fastapi import APIRouter, UploadFile, File, Query, Body

router = APIRouter()
FileService = ServiceProvider.get_file_service()

@router.post("/upload", response_model=FileModel)
async def upload_file(file: UploadFile = File(...), sub_path: str = Form(None)):
    """
    Téléverse un fichier dans le dossier prévu.
    """
    return await FileService.save_file(file, sub_path=sub_path)

@router.get("/list", response_model=FolderModel)
async def get_files(path: str = Query(default=".", description="Chemin relatif à partir du dossier racine")):
    """
    Récupère l'arborescence de fichiers et dossiers à partir du chemin donné.
    """
    return await FileService.list_directory(path)

@router.delete("/remove/{item_id}", response_model=bool)
async def remove_file_or_folder(item_id: str):
    """
    Supprime un fichier ou un dossier à partir de son ID.
    """
    return await FileService.delete_path(item_id)

@router.put("/rename/{item_id}", response_model=bool)
async def rename_file_or_folder(item_id: str, new_name: str = Body(..., embed=True)):
    """
    Renomme un fichier ou un dossier à partir de son ID.
    """
    print(new_name)
    return await FileService.rename_path(item_id, new_name)

@router.post("/create-directory", response_model=bool)
async def create_directory(
    name: str = Body(...),
    sub_path: str = Body(...)
):
    """
    Crée un nouveau dossier à l'emplacement spécifié.
    """
    return await FileService.create_directory(name, sub_path)



