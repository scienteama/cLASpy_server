from pathlib import Path
from typing import Annotated, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.params import Form
from app.core.service_provider import ServiceProvider
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
    fileInfos: dict | None = None

    # Sauvegarde le fichier sur le serveur si keepOnServer=True
    if keepOnServer:
        if folderId.lower() == "root":
            parent_id = None
        else:
            parent_id = folderId
        res = await file_service.save_file(file, user_id, db, parent_id)
        fileInfos = {
            "full_path": await file_service.compute_physical_path_async(db, res.saved_as, file_service.storage_root),
            "name": res.name
        }

    infos = await claspyML_service.load_data_file(file, fileInfos)

    return ApiResponse[str](data=infos)
