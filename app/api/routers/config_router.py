from typing import Annotated
from fastapi import APIRouter, Depends
from app.core.provider import get_config_service
from app.schemas.response_schema import ApiResponse
from app.services.config_service import ConfigService


router = APIRouter()


@router.get("/load", response_model=ApiResponse[dict])
async def get_api_settings(conf_service: Annotated[ConfigService, Depends(get_config_service)],) -> dict:
    api_settings = await conf_service.get_api_settings()
    return ApiResponse[dict](data=api_settings)
