from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.auth_utils import raise_auth_exception, verify_token

PUBLIC_ROUTES = {
    "/api/auth/login",
    "/api/auth/check-session",
    "/api/modules/list/claspy-modules",
}


class AuthMiddleware(BaseHTTPMiddleware):

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):

        if request.method == "OPTIONS":
            return await call_next(request)

        if request.url.path in PUBLIC_ROUTES:
            return await call_next(request)

        token = request.cookies.get("token") or request.headers.get("Authorization")
        if not token:
            raise_auth_exception("Token manquant")

        user_data = verify_token(token)
        if not user_data:
            raise_auth_exception("Token invalide")

        # Attach user to request
        request.state.user = user_data

        return await call_next(request)
