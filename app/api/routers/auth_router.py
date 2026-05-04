from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response
from app.core.config import get_settings
from app.core.oauth import OAuth2EmailRequestForm
from app.core.provider import get_auth_service
from app.schemas.response_schema import ApiResponse
from app.schemas.auth_schema import AuthResponse, CookieConfig, Token, set_http_only_cookie
from app.services.auth_service import AuthService
from app.utils.auth_utils import verify_token

router = APIRouter()


@router.post("/login", response_model=ApiResponse[Token])
async def login_for_access_token(
    res: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    form_data: Annotated[OAuth2EmailRequestForm, Depends()],
) -> Token:
    config = get_settings()
    user = await auth_service.authenticate(form_data.email, form_data.password)
    token = await auth_service.create_access_token(user)
    set_http_only_cookie(
        res,
        CookieConfig(
            key="token",
            value=token.access_token,
            max_age_minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES,
        ),
    )
    return ApiResponse[Token](data=token)


@router.post("/logout", response_model=ApiResponse[str])
async def logout(
    res: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    result = await auth_service.clear_auth_cookie(res, "token")
    return ApiResponse[str](data=result)


@router.get("/check-session", response_model=ApiResponse[AuthResponse])
async def check_session(request: Request):
    token = request.cookies.get("token")

    if not token:
        return ApiResponse(data=AuthResponse(isAuthenticated=False, exp=0, sessionUserData=None))

    token_data, exp = verify_token(token)

    return ApiResponse(data=AuthResponse(isAuthenticated=True, exp=exp, sessionUserData=token_data))
