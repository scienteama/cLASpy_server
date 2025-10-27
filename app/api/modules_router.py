from typing import List
from fastapi import APIRouter, HTTPException
from app.core.service_provider import ServiceProvider
from app.schemas.module_schema import ClaspyModule
from app.schemas.response_schema import ApiResponse

router = APIRouter()
modules_service = ServiceProvider.get_modules_service()

@router.post("/load/{plugin_name}", response_model=ApiResponse[str])
def load_claspy_plugin(plugin_name: str):
    result = modules_service.load_plugin(plugin_name)
    return ApiResponse[str](data=result)

@router.delete("/unload/{plugin_name}", response_model=ApiResponse[str])
def unload_claspy_plugin(plugin_name: str):
    result = modules_service.unload_plugin(plugin_name.lower())
    return ApiResponse[str](data=result)

@router.get("/list/claspy-modules", response_model=ApiResponse[List[ClaspyModule]])
def get_i_claspy_modules():
    claspy_modules = modules_service.list_claspy_modules()
    return ApiResponse[List[ClaspyModule]](data=claspy_modules)

