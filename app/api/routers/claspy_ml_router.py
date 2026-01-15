from typing import Annotated, Dict, List
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.params import Form
from app.core.provider import get_claspyml_service, get_file_service
from app.schemas.response_schema import ApiResponse
from app.schemas.sklearn_schema import AlgoParam, AlgoParamsResponse
from app.services.claspy_ml_service import ClaspyMLService
from app.services.files_service import FileService

router = APIRouter()


@router.get("/core_version")
def get_claspy_ml_core_version(claspyML_service: Annotated[ClaspyMLService, Depends(get_claspyml_service)]) -> str:
    version = claspyML_service.get_core_version()
    return version


@router.get("/algorithms/{name}/params", response_model=ApiResponse[Dict[str, AlgoParam]])
def get_algo_params(name: str, claspyML_service: Annotated[ClaspyMLService, Depends(get_claspyml_service)]):
    params_dict = claspyML_service.get_algorithm_parameters(name)
    model_params = AlgoParamsResponse(root=params_dict)
    return ApiResponse[Dict[str, AlgoParam]](data=model_params.model_dump())


@router.get("/algorithms", response_model=ApiResponse[List[str]])
def get_algorithms(claspyML_service: Annotated[ClaspyMLService,
                   Depends(get_claspyml_service)]):
    algos = claspyML_service.get_all_algorithms()
    return ApiResponse[List[str]](data=algos)


@router.post("/load-data", response_model=ApiResponse[dict])
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
    result = await claspyML_service.process_file(req, keepOnServer, folderId, file)
    return ApiResponse[dict](data=result)
