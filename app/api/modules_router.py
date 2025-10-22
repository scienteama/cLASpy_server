from fastapi import APIRouter
from app.core.service_provider import ServiceProvider

router = APIRouter()
ModulesService = ServiceProvider.get_modules_service()

@router.post("/load/{plugin_name}")
def load_claspy_plugin(plugin_name: str):
    pPath = ModulesService.load_plugin(plugin_name)
    return {"message": f"Plugin '{plugin_name}' chargé avec succès depuis {pPath}"}

@router.post("/unload/{plugin_name}")
def unload_claspy_plugin(plugin_name: str):
    ModulesService.unload_plugin(plugin_name)
    return {"message": f"Plugin '{plugin_name}' déchargé avec succès."}

@router.get("/list/installed_modules")
def get_i_claspy_modules():
    claspy_modules = ModulesService.list_installed_claspy_modules()
    return claspy_modules