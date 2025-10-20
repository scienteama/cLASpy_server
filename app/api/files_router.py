from fastapi.params import Form
from app.schemas.file_schema import FileModel, FolderModel
from app.services import files_service as fileService
from fastapi import APIRouter, UploadFile, File, Query, Body
from typing import List

router = APIRouter()

@router.post("/upload", response_model=FileModel)
async def upload_file(file: UploadFile = File(...), sub_path: str = Form(None)):
    """
    Téléverse un fichier dans le dossier prévu.
    """
    return await fileService.save_file(file, sub_path=sub_path)

@router.get("/list", response_model=FolderModel)
async def get_files(path: str = Query(default=".", description="Chemin relatif à partir du dossier racine")):
    """
    Récupère l'arborescence de fichiers et dossiers à partir du chemin donné.
    """
    return await fileService.list_directory(path)

@router.delete("/remove/{item_id}", response_model=bool)
async def remove_file_or_folder(item_id: str):
    """
    Supprime un fichier ou un dossier à partir de son ID.
    """
    print('test')
    return await fileService.delete_path(item_id)

@router.put("/rename/{item_id}", response_model=bool)
async def rename_file_or_folder(item_id: str, new_name: str = Body(..., embed=True)):
    """
    Renomme un fichier ou un dossier à partir de son ID.
    """
    print('test')
    print(new_name)
    return await fileService.rename_path(item_id, new_name)

@router.post("/create-directory", response_model=bool)
async def create_directory(
    name: str = Body(...),
    subPath: str = Body(...)
):
    """
    Crée un nouveau dossier à l'emplacement spécifié.
    """
    return await fileService.create_directory(name, subPath)



