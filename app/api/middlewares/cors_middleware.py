from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp
import os


class CORSMiddleware(BaseHTTPMiddleware):
    """
    Middleware CORS
    Gère les règles Cross-Origin (front ↔ backend).
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

        env = os.getenv("ENV", "development")

        if env == "production":
            self.allow_origins = {""} #TODO à remplacer
        else:
            self.allow_origins = {"https://localhost:8081", "https://127.0.0.1:8081"}

        self.allow_methods = {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"}
        self.allow_headers = {"Authorization", "Content-Type"}
        self.allow_credentials = True

    async def dispatch(self, request, call_next):
        origin = request.headers.get("origin")

        response: Response

        if request.method == "OPTIONS":
            response = Response(status_code=200)
        else:
            response = await call_next(request)

        if origin in self.allow_origins or "*" in self.allow_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
            response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
            if self.allow_credentials:
                response.headers["Access-Control-Allow-Credentials"] = "true"

        return response
