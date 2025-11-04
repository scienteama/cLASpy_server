from typing import Annotated
from fastapi import Depends, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.service_provider import ServiceProvider
from app.schemas.error_schema import ErrorResponse
from app.services.interfaces.auth_interface import IAuthService
from app.utils.auth_utils import raise_auth_exception

PUBLIC_ROUTES = {
    "/api/auth/login",
    "/api/auth/check-session",
    "/api/modules/list/claspy-modules",
}

class AuthMiddleware(BaseHTTPMiddleware):

    def __init__(self, app):
        super().__init__(app)
        self.auth_service: IAuthService = ServiceProvider.get_auth_service()
      
    async def dispatch(self,
                       request: Request,
                       call_next):
        try:
            if request.method == "OPTIONS":
                return await call_next(request)

            if request.url.path in PUBLIC_ROUTES:
                return await call_next(request)

            token = request.cookies.get("token") or request.headers.get("Authorization")
            if not token:
                raise_auth_exception("Token manquant")

            user_data = self.auth_service.verify_token(token)
            if not user_data:
                raise_auth_exception("Token invalide")

            # Attach user to request
            request.state.user = user_data

            return await call_next(request)

        except HTTPException as exc:
            response = ErrorResponse.http_exception_handler(request, exc)
        except Exception as exc:
            response = ErrorResponse.generic_exception_handler(request, exc)

        return response
