from fastapi import APIRouter
from app.core.service_provider import ServiceProvider

router = APIRouter()
Claspy_ML_Service = ServiceProvider.get_claspy_ML_service()

@router.get("/core_version")
def get_claspy_ml_core_version() -> str:
    version = Claspy_ML_Service.get_core_version()
    return version