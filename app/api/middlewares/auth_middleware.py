from fastapi import HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.service_provider import ServiceProvider
from app.schemas.error_schema import ErrorResponse
from app.utils.auth_utils import raise_auth_exception

ALLOWED_ORIGINS = {"https://localhost:8081",
                   "https://127.0.0.1:8081"}

PUBLIC_ROUTES   = {"/api/auth/login",
                   "/api/auth/check-session",
                   "/api/modules/list/claspy-modules"}

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            if request.url.path in PUBLIC_ROUTES:
                return await call_next(request)

            token = request.cookies.get("token") or request.headers.get("Authorization")

            if not token:
                raise_auth_exception("Token manquant")

            auth_service = ServiceProvider.get_auth_service()
            userData = auth_service.verify_token(token)

            if userData:
                request.state.user = userData

            return await call_next(request)

        except HTTPException as exc:
            response = ErrorResponse.http_exception_handler(request, exc)
        except Exception as exc:
            response = ErrorResponse.generic_exception_handler(request, exc)

        origin = request.headers.get("origin")
        if origin in ALLOWED_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"

        return response
