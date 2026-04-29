from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response
from app.core.oauth import OAuth2EmailRequestForm
from app.core.provider import get_auth_service
from app.schemas.response_schema import ApiResponse
from app.schemas.auth_schema import CookieConfig, Token, set_http_only_cookie
from app.services.auth_service import AuthService
from app.utils.auth_utils import verify_token

router = APIRouter()


@router.post("/login", response_model=ApiResponse[Token])
async def login_for_access_token(
    res: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    form_data: Annotated[OAuth2EmailRequestForm, Depends()],
) -> Token:
    user = await auth_service.authenticate(form_data.email, form_data.password)
    token = await auth_service.create_access_token(user)
    set_http_only_cookie(res, CookieConfig(key="token", value=token.access_token))
    return ApiResponse[Token](data=token)


@router.post("/logout", response_model=ApiResponse[str])
async def logout(
    res: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    result = await auth_service.clear_auth_cookie(res, "token")
    return ApiResponse[str](data=result)


@router.get("/check-session", response_model=ApiResponse[dict])
async def check_session(
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    token = request.cookies.get("token")
    if not token:
        return ApiResponse[dict](data={"isAuthenticated": False})
    else:
        verify_token(token)
        return ApiResponse[dict](data={"isAuthenticated": True})
