from typing import Annotated
from fastapi.params import Form
from app.core.service_provider import ServiceProvider
from app.database import get_async_db
from app.schemas.file_schema import FileModel, FolderModel
from fastapi import APIRouter, Depends, Request, UploadFile, File, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.response_schema import ApiResponse
from app.services.interfaces.files_interface import IFileService

router = APIRouter()

@router.post("/upload", response_model=ApiResponse[FileModel], )
async def upload_file(req: Request,
                      file_service: Annotated[IFileService, Depends(lambda: ServiceProvider.get_file_service())],
                      db: AsyncSession = Depends(get_async_db),
                      file: UploadFile = File(...),
                      sub_path: str = Form(None)):
    """
    Téléverse un fichier dans le dossier prévu.
    """
    user_id = int(req.state.user.id)
    res = await file_service.save_file(file, user_id, db, sub_path=sub_path)
    return ApiResponse[FileModel](data=res)

@router.get("/list", response_model=ApiResponse[FolderModel])
async def get_files(req: Request,
                    file_service: Annotated[IFileService, Depends(lambda: ServiceProvider.get_file_service())],
                    db: AsyncSession = Depends(get_async_db),
                    path: str = Query(default=".", description="Chemin relatif à partir du dossier racine")):
    """
    Récupère l'arborescence de fichiers et dossiers à partir du chemin donné.
    """
    user_id = int(req.state.user.id)
    res = await file_service.list_directory(user_id, db, path )
    return ApiResponse[FolderModel](data=res)

@router.delete("/remove/{item_id}", response_model=ApiResponse[str])
async def remove_file_or_folder(item_id: str, file_service: Annotated[IFileService, Depends(lambda: ServiceProvider.get_file_service())]):
    """
    Supprime un fichier ou un dossier à partir de son ID.
    """
    res = await file_service.delete_path(item_id)
    return ApiResponse[str](data=res)

@router.put("/rename/{item_id}", response_model=ApiResponse[str])
async def rename_file_or_folder(item_id: str,
                                file_service: Annotated[IFileService, Depends(lambda: ServiceProvider.get_file_service())],
                                new_name: str = Body(..., embed=True)):
    """
    Renomme un fichier ou un dossier à partir de son ID.
    """
    res = await file_service.rename_path(item_id, new_name)
    return ApiResponse(data=str(res))

@router.post("/create-directory", response_model=ApiResponse[str])
async def create_directory(req: Request,
                           file_service: Annotated[IFileService, Depends(lambda: ServiceProvider.get_file_service())],
                           db: AsyncSession = Depends(get_async_db),
                           name: str = Body(...),
                           sub_path: str = Body(...)):
    """
    Crée un nouveau dossier à l'emplacement spécifié.
    """
    user_id = int(req.state.user.id)
    res = await file_service.create_directory(user_id, name, db, sub_path)
    return ApiResponse(data=str(res))



