from typing import Dict, List
from fastapi import APIRouter
from app.core.service_provider import ServiceProvider
from app.schemas.response_schema import ApiResponse
from app.schemas.sklearn_schema import AlgoParam, AlgoParamsResponse

router = APIRouter()
claspy_ml_service = ServiceProvider.get_claspy_ML_service()

@router.get("/core_version")
def get_claspy_ml_core_version() -> str:
    version = claspy_ml_service.get_core_version()
    return version

@router.get("/algorithms/{name}/params", response_model=ApiResponse[Dict[str, AlgoParam]])
def get_algo_params(name: str):
    params_dict = claspy_ml_service.get_algorithm_parameters(name)
    model_params = AlgoParamsResponse(root=params_dict)
    return ApiResponse[Dict[str, AlgoParam]](data=model_params.model_dump())

@router.get("/algorithms", response_model=ApiResponse[List[str]])
def get_algorithms():
    algos = claspy_ml_service.get_all_algorithms()
    return ApiResponse[List[str]](data=algos)
