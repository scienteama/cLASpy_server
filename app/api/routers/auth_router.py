from fastapi import Body
from app.schemas.auth_schema import PasswordResetRequest
from http import HTTPStatus
from fastapi import HTTPException
from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response
from app.core.config import get_settings
from app.core.oauth import OAuth2EmailRequestForm
from app.core.provider import get_auth_service
from app.schemas.response_schema import ApiResponse
from app.schemas.auth_schema import AuthResponse, CookieConfig, Token, set_http_only_cookie
from app.services.auth_service import AuthService
from app.utils.auth_utils import extract_token, verify_token

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

    token = extract_token(request)
    if not token:
        return ApiResponse(data=AuthResponse(isAuthenticated=False, exp=0, sessionUserData=None))

    token_data, exp = verify_token(token)

    return ApiResponse(data=AuthResponse(isAuthenticated=True, exp=exp, sessionUserData=token_data))


@router.post("/reset-password", response_model=ApiResponse[str])
async def reset_password(
    auth_service: AuthService = Depends(get_auth_service),
    form_data: PasswordResetRequest = Body(...),
) -> ApiResponse[str]:

    if not form_data.recovery_code and not form_data.reset_token:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Fournissez soit un recoveryCode, soit un resetToken",
        )

    try:
        if form_data.recovery_code:
            result = await auth_service.reset_with_recovery_code(
                form_data.email, form_data.recovery_code, form_data.new_password
            )
        elif form_data.reset_token:
            result = await auth_service.reset_with_token(
                form_data.email, form_data.reset_token, form_data.new_password
            )

        return ApiResponse[str](data=result)

    except ValueError as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        auth_service.log.error(f"Password reset failed: {str(e)}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
