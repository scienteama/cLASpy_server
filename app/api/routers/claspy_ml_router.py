import asyncio
from pathlib import Path
from typing import Annotated, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.params import Form
from app.core.service_provider import ServiceProvider
from app.dao.file_dao import FileDAO
from app.database import get_async_db
from app.schemas.response_schema import ApiResponse
from app.schemas.sklearn_schema import AlgoParam, AlgoParamsResponse
from app.services.interfaces.claspyml_interface import IClaspyMLService
from app.services.interfaces.files_interface import IFileService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/core_version")
def get_claspy_ml_core_version(claspyML_service: Annotated[IClaspyMLService, Depends(
        lambda: ServiceProvider.get_claspyml_service())]) -> str:
    version = claspyML_service.get_core_version()
    return version


@router.get("/algorithms/{name}/params", response_model=ApiResponse[Dict[str, AlgoParam]])
def get_algo_params(name: str, claspyML_service: Annotated[IClaspyMLService, Depends(
        lambda: ServiceProvider.get_claspyml_service())]):
    params_dict = claspyML_service.get_algorithm_parameters(name)
    model_params = AlgoParamsResponse(root=params_dict)
    return ApiResponse[Dict[str, AlgoParam]](data=model_params.model_dump())


@router.get("/algorithms", response_model=ApiResponse[List[str]])
def get_algorithms(claspyML_service: Annotated[IClaspyMLService,
                   Depends(lambda: ServiceProvider.get_claspyml_service())]):
    algos = claspyML_service.get_all_algorithms()
    return ApiResponse[List[str]](data=algos)


@router.post("/load-data", response_model=ApiResponse[str])
async def load_data_file(
    req: Request,
    claspyML_service: Annotated[IClaspyMLService, Depends(lambda: ServiceProvider.get_claspyml_service())],
    file_service: Annotated[IFileService, Depends(lambda: ServiceProvider.get_file_service())],
    db: AsyncSession = Depends(get_async_db),
    file: UploadFile = File(...),
    keepOnServer: bool = Form(...),
    folderId: str = Form(...)
):
    """
    Charge un fichier de données (.las ou .csv) et retourne des informations sur le nuage de points.
    """
    user_id = int(req.state.user.id)
    role_id = int(req.state.user.role_id)
    fileInfos: dict | None = None

    print(f"keepOnServer: {keepOnServer}, folderId: {folderId}")

    # Sauvegarde le fichier sur le serveur si keepOnServer=True
    if keepOnServer:
        if folderId.lower() == "root":
            parent_id = None
        else:
            parent_id = folderId
        res = await file_service.save_file(file, user_id, role_id, db, parent_id)
        
        _file = await FileDAO.get_file(db, res.id)

        fileInfos = {
            "full_path": await file_service.compute_physical_path_async(db, _file, file_service.storage_root),
            "name": res.name
        }

    stdout = await claspyML_service.load_data_file(file, fileInfos)

    return ApiResponse[str](data=stdout)

# from fastapi.responses import StreamingResponse
# @router.post("/load-data")
# async def load_data_file_stream(
#     req: Request,
#     claspyML_service: Annotated[IClaspyMLService, Depends(lambda: ServiceProvider.get_claspyml_service())],
#     file_service: Annotated[IFileService, Depends(lambda: ServiceProvider.get_file_service())],
#     db: AsyncSession = Depends(get_async_db),
#     file: UploadFile = File(...),
#     keepOnServer: bool = Form(...),
#     folderId: str = Form(...)
# ):
#     user_id = int(req.state.user.id)
#     role_id = int(req.state.user.role_id)
#     fileInfos: dict | None = None

#     # Sauvegarde sur le serveur si demandé
#     if keepOnServer:
#         parent_id = None if folderId.lower() == "root" else folderId
#         res = await file_service.save_file(file, user_id, role_id, db, parent_id)
#         _file = await FileDAO.get_file(db, res.id)
#         fileInfos = {
#             "full_path": await file_service.compute_physical_path_async(db, _file, file_service.storage_root),
#             "name": res.name
#         }

#     # Generator pour streamer la sortie de ML
#     async def stream():
#         async for line in claspyML_service.load_data_file_stream(file, fileInfos):
#             yield f"data: {line}\n\n"
#             await asyncio.sleep(0)  # permet à l'event loop de respirer

#     return StreamingResponse(stream(), media_type="text/event-stream")

