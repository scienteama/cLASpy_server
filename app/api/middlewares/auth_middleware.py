from fastapi import HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.service_provider import ServiceProvider
from app.schemas.error_schema import ErrorResponse
from app.utils.auth_utils import raise_auth_exception

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            token = request.cookies.get("access_token") or request.headers.get("Authorization")

            if not token:
                raise_auth_exception("Token manquant")

            if token.startswith("Bearer "):
                token = token.split(" ")[1]

            auth_service = ServiceProvider.get_auth_service()
            auth_service.verify_token(token)

            response = await call_next(request)
            return response

        except HTTPException as exc:
            return ErrorResponse.http_exception_handler(request, exc)

        except Exception as exc:
            return ErrorResponse.generic_exception_handler(request, exc)