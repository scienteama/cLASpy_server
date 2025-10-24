from fastapi.params import Form
from app.schemas.file_schema import FileModel, FolderModel
from app.core.service_provider import ServiceProvider
from fastapi import APIRouter, UploadFile, File, Query, Body

from app.schemas.response_schema import ApiResponse

router = APIRouter()
FileService = ServiceProvider.get_file_service()

@router.post("/upload", response_model=ApiResponse[FileModel])
async def upload_file(file: UploadFile = File(...), sub_path: str = Form(None)):
    """
    Téléverse un fichier dans le dossier prévu.
    """
    res = await FileService.save_file(file, sub_path=sub_path)
    return ApiResponse[FileModel](data=res)

@router.get("/list", response_model=ApiResponse[FolderModel])
async def get_files(path: str = Query(default=".", description="Chemin relatif à partir du dossier racine")):
    """
    Récupère l'arborescence de fichiers et dossiers à partir du chemin donné.
    """
    res = await FileService.list_directory(path)
    return ApiResponse[FolderModel](data=res)

@router.delete("/remove/{item_id}", response_model=ApiResponse[str])
async def remove_file_or_folder(item_id: str):
    """
    Supprime un fichier ou un dossier à partir de son ID.
    """
    res = await FileService.delete_path(item_id)
    return ApiResponse[str](data=res)

@router.put("/rename/{item_id}", response_model=ApiResponse[str])
async def rename_file_or_folder(item_id: str, new_name: str = Body(..., embed=True)):
    """
    Renomme un fichier ou un dossier à partir de son ID.
    """
    res = await FileService.rename_path(item_id, new_name)
    return ApiResponse(data=str(res))

@router.post("/create-directory", response_model=ApiResponse[str])
async def create_directory(name: str = Body(...), sub_path: str = Body(...)):
    """
    Crée un nouveau dossier à l'emplacement spécifié.
    """
    res = await FileService.create_directory(name, sub_path)
    return ApiResponse(data=str(res))



