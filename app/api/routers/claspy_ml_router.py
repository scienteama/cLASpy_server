from typing import Annotated, Dict, List
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.params import Form
from app.core.provider import get_claspyml_service, get_file_service
from app.schemas.response_schema import ApiResponse
from app.schemas.sklearn_schema import AlgoParam, AlgoParamsResponse
from app.schemas.train_schema import PointCloudInfo
from app.services.claspy_ml_service import ClaspyMLService
from app.services.files_service import FileService

router = APIRouter()


@router.get("/core_version")
def get_claspy_ml_core_version(claspyML_service: Annotated[ClaspyMLService, Depends(get_claspyml_service)]) -> str:
    version = claspyML_service.get_core_version()
    return version


@router.get("/algorithms/{name}/params", response_model=ApiResponse[AlgoParamsResponse])
def get_algo_params(name: str, claspyML_service: Annotated[ClaspyMLService, Depends(get_claspyml_service)]):
    params_dict, description = claspyML_service.get_algorithm_parameters(name)
    
    # Convertit chaque paramètre en AlgoParam
    model_params = {k: AlgoParam(**v) for k, v in params_dict.items()}

    response = AlgoParamsResponse(
        description=description,
        parameters=model_params
    )

    return ApiResponse[AlgoParamsResponse](data=response)


@router.get("/algorithms", response_model=ApiResponse[List[str]])
def get_algorithms(claspyML_service: Annotated[ClaspyMLService,
                   Depends(get_claspyml_service)]):
    algos = claspyML_service.get_all_algorithms()
    return ApiResponse[List[str]](data=algos)


@router.post("/load-data", response_model=ApiResponse[PointCloudInfo])
async def load_data_file(
    req: Request,
    claspyML_service: Annotated[ClaspyMLService, Depends(get_claspyml_service)],
    file: UploadFile = File(...),
    keepOnServer: bool = Form(...),
    folderId: str = Form(...)
):
    """
    Charge un fichier de données (.las ou .csv) et retourne des informations sur le nuage de points.
    """
    result = await claspyML_service.upload_file(req, keepOnServer, folderId, file)
    return ApiResponse[PointCloudInfo](data=result)

@router.get('/load-file/{file_id}', response_model=ApiResponse[PointCloudInfo])
async def load_existing_file(
    req: Request,
    file_id: str,
    claspyML_service: Annotated[ClaspyMLService, Depends(get_claspyml_service)]
):
    """
    Charge un fichier de données déjà existant (.las ou .csv) et retourne des informations sur le nuage de points.
    """

    result = await claspyML_service.load_file(file_id)
    return ApiResponse[PointCloudInfo](data=result)
