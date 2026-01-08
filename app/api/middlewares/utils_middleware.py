import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import os


class UtilsMiddleware(BaseHTTPMiddleware):
    """
    Middlewares utilitaires.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.env = os.getenv("ENV", "development")

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.6f}"
        return response
