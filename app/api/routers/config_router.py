from typing import Annotated
from fastapi import APIRouter, Depends
from app.core.provider import get_config_service, get_user_service
from app.schemas.response_schema import ApiResponse
from app.services.config_service import ConfigService
from app.services.users_service import UserService

router = APIRouter()


@router.get("/load", response_model=ApiResponse[dict])
async def get_api_settings(
    conf_service: Annotated[ConfigService, Depends(get_config_service)],
) -> dict:
    api_settings = await conf_service.get_api_settings()
    return ApiResponse[dict](data=api_settings)


@router.get("/first-launch-completed", response_model=ApiResponse[dict])
async def get_setup_status(
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> dict:
    users = await user_service.get_user_count()
    setup_status = {"first_launch_completed": users > 0}
    return ApiResponse[dict](data=setup_status)
