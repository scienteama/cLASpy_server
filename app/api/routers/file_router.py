from typing import Annotated
from fastapi import APIRouter, Depends, Request, UploadFile, File, Body, Query
from fastapi.params import Form
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.service_provider import ServiceProvider
from app.database import get_async_db
from app.schemas.file_schema import FileModel, FolderModel
from app.schemas.response_schema import ApiResponse
from app.services.interfaces.files_interface import IFileService

router = APIRouter()

# ------------------------
# Upload file
# ------------------------
@router.post("/upload", response_model=ApiResponse[FileModel])
async def upload_file(
    req: Request,
    file_service: Annotated[IFileService, Depends(lambda: ServiceProvider.get_file_service())],
    db: AsyncSession = Depends(get_async_db),
    file: UploadFile = File(...),
    parent_id: UUID | None = Form(None),  # remplace sub_path
):
    """
    Téléverse un fichier dans le dossier parent spécifié (parent_id).
    """
    user_id = int(req.state.user.id)
    res = await file_service.save_file(file, user_id, db, parent_id=parent_id)
    return ApiResponse[FileModel](data=res)

# ------------------------
# List directory
# ------------------------
@router.get("/list", response_model=ApiResponse[FolderModel])
async def get_files(
    req: Request,
    file_service: Annotated[IFileService, Depends(lambda: ServiceProvider.get_file_service())],
    db: AsyncSession = Depends(get_async_db),
    parent_id: UUID | None = Query(None, description="ID du dossier parent"),
):
    """
    Récupère l'arborescence de fichiers et dossiers à partir du dossier parent.
    """
    user_id = int(req.state.user.id)
    role_id = int(req.state.user.role_id)
    res = await file_service.list_directory(user_id, role_id, db, parent_id=parent_id)
    return ApiResponse[FolderModel](data=res)

# ------------------------
# Remove file / folder
# ------------------------
@router.delete("/remove/{item_id}", response_model=ApiResponse[str])
async def remove_file_or_folder(
    item_id: UUID,
    file_service: Annotated[IFileService, Depends(lambda: ServiceProvider.get_file_service())],
    db: AsyncSession = Depends(get_async_db),
):
    """
    Supprime un fichier ou un dossier à partir de son ID (soft delete).
    """
    res = await file_service.delete_path(item_id, db)
    return ApiResponse[str](data=res)

# ------------------------
# Rename file / folder
# ------------------------
@router.put("/rename/{item_id}", response_model=ApiResponse[str])
async def rename_file_or_folder(
    item_id: UUID,
    file_service: Annotated[IFileService, Depends(lambda: ServiceProvider.get_file_service())],
    db: AsyncSession = Depends(get_async_db),
    new_name: str = Body(..., embed=True),
):
    """
    Renomme un fichier ou un dossier à partir de son ID.
    """
    res = await file_service.rename_path(item_id, new_name, db)
    return ApiResponse[str](data=res)

# ------------------------
# Create directory
# ------------------------
@router.post("/create-directory", response_model=ApiResponse[str])
async def create_directory(
    req: Request,
    file_service: Annotated[IFileService, Depends(lambda: ServiceProvider.get_file_service())],
    db: AsyncSession = Depends(get_async_db),
    name: str = Body(...),
    parent_id: UUID | None = Body(None),
):
    """
    Crée un nouveau dossier dans le dossier parent spécifié.
    """
    user_id = int(req.state.user.id)
    res = await file_service.create_directory(user_id, name, db, parent_id=parent_id)
    return ApiResponse[str](data=res)
