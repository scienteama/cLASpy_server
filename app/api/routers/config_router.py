from typing import Annotated
from fastapi import APIRouter, Depends, Response
from app.core.config import Settings
from app.core.service_provider import ServiceProvider
from app.schemas.response_schema import ApiResponse
from app.services.interfaces.config_interface import IConfigService

router = APIRouter()

@router.get("/load", response_model=ApiResponse[dict])
async def get_api_settings(conf_service: Annotated[IConfigService, Depends(lambda: ServiceProvider.get_config_service())],) -> dict:
    api_settings = await conf_service.get_api_settings()
    return ApiResponse[dict](data=api_settings)


