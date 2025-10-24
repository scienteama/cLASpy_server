from typing import List
from fastapi import APIRouter, HTTPException
from app.core.service_provider import ServiceProvider
from app.schemas.module_schema import ClaspyModule

router = APIRouter()
ModulesService = ServiceProvider.get_modules_service()

@router.post("/load/{plugin_name}")
def load_claspy_plugin(plugin_name: str):
    return ModulesService.load_plugin(plugin_name)

@router.delete("/unload/{plugin_name}")
def unload_claspy_plugin(plugin_name: str):
    ModulesService.unload_plugin(plugin_name.lower())
    return {"message": f"Plugin '{plugin_name}' déchargé avec succès."}

@router.get("/list/claspy-modules", response_model=List[ClaspyModule])
def get_i_claspy_modules():
    claspy_modules = ModulesService.list_claspy_modules()
    return claspy_modules

