from typing import Annotated, Dict, List
from fastapi import APIRouter, Depends
from app.core.service_provider import ServiceProvider
from app.schemas.response_schema import ApiResponse
from app.schemas.sklearn_schema import AlgoParam, AlgoParamsResponse
from app.services.interfaces.claspyml_interface import IClaspyMLService

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
