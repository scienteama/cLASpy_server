from http import HTTPStatus
from typing import Annotated, List
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Body, Query
from fastapi.params import Form
from fastapi.responses import FileResponse
from uuid import UUID
from app.core.provider import get_file_service
from app.schemas.file_schema import FileModel, FolderModel
from app.schemas.response_schema import ApiResponse
from app.services.files_service import FileService


router = APIRouter()

# ------------------------
# Upload file
# ------------------------


@router.post("/upload", response_model=ApiResponse[FileModel])
async def upload_file(
    req: Request,
    file_service: Annotated[FileService, Depends(get_file_service)],
    file: UploadFile = File(...),
    parent_id: UUID | None = Form(None),
):
    """
    Téléverse un fichier dans le dossier parent spécifié (parent_id).
    """
    user_id = int(req.state.user.id)
    role_id = int(req.state.user.role_id)
    res = await file_service.save_file(file, user_id, role_id, parent_id=parent_id)
    return ApiResponse[FileModel](data=res)


# ------------------------
# Download file
# ------------------------


@router.get("/download-file/{item_id}", response_class=FileResponse)
async def download_file(
    item_id: UUID,
    file_service: Annotated[FileService, Depends(get_file_service)]
):
    """
    Télécharger un fichier.
    """
    try:
        return await file_service.download_file(item_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du téléchargement: {str(e)}"
        )


# ------------------------
# List directory
# ------------------------


@router.get("/list", response_model=ApiResponse[FolderModel])
async def get_files(
    req: Request,
    file_service: Annotated[FileService, Depends(get_file_service)],
    parent_id: UUID | None = Query(None, description="ID du dossier parent"),
):
    """
    Récupère l'arborescence de fichiers et dossiers à partir du dossier parent.
    """
    user_id = int(req.state.user.id)
    role_id = int(req.state.user.role_id)
    res = await file_service.list_directory(user_id, role_id, parent_id=parent_id)
    return ApiResponse[FolderModel](data=res)


# ------------------------
# Remove file / folder
# ------------------------

@router.delete("/remove/{item_id}", response_model=ApiResponse[str])
async def remove_file_or_folder(
    req: Request,
    item_id: UUID,
    file_service: Annotated[FileService, Depends(get_file_service)],
):
    """
    Supprime un fichier ou un dossier à partir de son ID (soft delete).
    """
    user_id = int(req.state.user.id)
    role_id = int(req.state.user.role_id)
    res = await file_service.delete_path(user_id, role_id, item_id)
    return ApiResponse[str](data=res)


# ------------------------
# Remove files
# ------------------------

@router.post("/remove-multiple", response_model=ApiResponse[str])
async def remove_items(
    req: Request,
    file_service: Annotated[FileService, Depends(get_file_service)],
    ids: List[uuid.UUID] = Body(...),
):
    user_id = int(req.state.user.id)
    role_id = int(req.state.user.role_id)

    try:
        for item_id in ids:
            await file_service.delete_path(
                user_id,
                role_id,
                item_id,
                auto_commit=False
            )

        await file_service.file_dao.commit()

        return ApiResponse[str](data=f"{len(ids)} élément(s) supprimé(s)")

    except Exception:
        await file_service.file_dao.rollback()
        raise


# -----------------------
# Rename file / folder
# ------------------------

@router.put("/rename/{item_id}", response_model=ApiResponse[str])
async def rename_file_or_folder(
    req: Request,
    item_id: UUID,
    file_service: Annotated[FileService, Depends(get_file_service)],
    new_name: str = Body(..., embed=True),
):
    """
    Renomme un fichier ou un dossier à partir de son ID.
    """
    user_id = int(req.state.user.id)
    role_id = int(req.state.user.role_id)
    res = await file_service.rename_path(item_id, user_id, role_id, new_name)
    return ApiResponse[str](data=res)


# ------------------------
# Create directory
# ------------------------

@router.post("/create-directory", response_model=ApiResponse[str])
async def create_directory(
    req: Request,
    file_service: Annotated[FileService, Depends(get_file_service)],
    name: str = Body(...),
    parent_id: UUID | None = Body(None),
):
    """
    Crée un nouveau dossier dans le dossier parent spécifié.
    """
    user_id = int(req.state.user.id)
    role_id = int(req.state.user.role_id)
    folder = await file_service.create_directory(user_id, role_id, name, parent_id=parent_id)
    return ApiResponse[str](data=f"Dossier {folder.logical_name} créé avec succès.")
