from typing import Annotated
from fastapi import APIRouter, Depends, Response
from app.core.oauth import OAuth2EmailRequestForm
from app.core.service_provider import ServiceProvider
from app.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.response_schema import ApiResponse
from app.schemas.auth_schema import CookieConfig, Token, set_http_only_cookie
from app.utils.auth_utils import raise_auth_exception

router = APIRouter()
auth_service = ServiceProvider.get_auth_service()

@router.post("/authenticate", response_model=ApiResponse[Token])
async def login_for_access_token( res: Response, form_data: Annotated[OAuth2EmailRequestForm, Depends()], db: AsyncSession = Depends(get_async_db)) -> Token:
    user = await auth_service.authenticate(form_data.email, form_data.password, db)
    if not user:
        raise_auth_exception("Email ou mot de passe incorrect")
    token = await auth_service.create_access_token(user)
    set_http_only_cookie(res, CookieConfig(key = 'token', value = token.access_token))
    return ApiResponse[Token](data=token)