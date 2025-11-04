from typing import Annotated, List
from fastapi import APIRouter, Depends
from app.core.service_provider import ServiceProvider
from app.schemas.module_schema import ClaspyModule
from app.schemas.response_schema import ApiResponse
from app.services.interfaces.module_interface import IModuleService

router = APIRouter()

@router.post("/load/{plugin_name}", response_model=ApiResponse[str])
def load_claspy_plugin(plugin_name: str, module_service: Annotated[IModuleService, Depends(lambda: ServiceProvider.get_module_service())]):
    result = module_service.load_plugin(plugin_name)
    return ApiResponse[str](data=result)

@router.delete("/unload/{plugin_name}", response_model=ApiResponse[str])
def unload_claspy_plugin(plugin_name: str, module_service: Annotated[IModuleService, Depends(lambda: ServiceProvider.get_module_service())]):
    result = module_service.unload_plugin(plugin_name.lower())
    return ApiResponse[str](data=result)

@router.get("/list/claspy-modules", response_model=ApiResponse[List[ClaspyModule]])
def get_i_claspy_modules(module_service: Annotated[IModuleService, Depends(lambda: ServiceProvider.get_module_service())]):
    claspy_modules = module_service.list_claspy_modules()
    return ApiResponse[List[ClaspyModule]](data=claspy_modules)

