from typing import Annotated, Any, List
from fastapi import APIRouter, Depends
from app.core.provider import get_module_service
from app.schemas.module_schema import ClaspyModule
from app.schemas.response_schema import ApiResponse
from app.services.modules_service import ModulesService

router = APIRouter()


@router.post("/load/{plugin_name}", response_model=ApiResponse[str])
async def load_claspy_plugin(plugin_name: str, module_service: Annotated[ModulesService, Depends(
        get_module_service)]):
    result = module_service.load_plugin(plugin_name)
    return ApiResponse[str](data=result)


@router.delete("/unload/{plugin_name}", response_model=ApiResponse[str])
async def unload_claspy_plugin(plugin_name: str, module_service: Annotated[ModulesService, Depends(
        get_module_service)]):
    result = module_service.unload_plugin(plugin_name.lower())
    return ApiResponse[str](data=result)


@router.get("/list/claspy-modules", response_model=ApiResponse[List[ClaspyModule]])
def get_i_claspy_modules(module_service: Annotated[ModulesService, Depends(get_module_service)]):
    claspy_modules = module_service.list_claspy_modules()
    return ApiResponse[List[ClaspyModule]](data=claspy_modules)


@router.get("/workers", response_model=ApiResponse[Any])
async def status_worker(module_service: Annotated[ModulesService, Depends(get_module_service)]):
    workers = await module_service.list_workers()
    return ApiResponse[Any](data=workers)
