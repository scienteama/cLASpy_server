from contextlib import asynccontextmanager
from http import HTTPStatus
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.registry import RouterRegistry
from app.database import engine
from app.api.users_router import router as users_router
from app.api.files_router import router as file_router
from app.api.modules_router import router as modules_router
from app.api.claspy_ml_router import router as claspy_ml_router
from app.schemas.error_schema import ErrorResponse

# Lifespan pour FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Création de la connexion à la DB au démarrage
    async with engine.begin() as conn:
        pass
    yield
    await engine.dispose()

# App FastAPI
app = FastAPI(lifespan=lifespan, title="cLASpy_T Web API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # à restreindre en prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enregistrement des routes
registry = RouterRegistry()
registry.register(modules_router, prefix="/api/modules", tags=["Modules"])
registry.register(users_router, prefix="/api/users", tags=["Users"])
registry.register(file_router, prefix="/api/files", tags=["Files"])
registry.register(claspy_ml_router, prefix="/api/claspy_ml", tags=["Claspy_ML"])
registry.include_all(app)

# HTTP Exception Handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    resp = ErrorResponse(
        isOk=False,
        result=HTTPStatus(exc.status_code).phrase,
        data={
            "detail": exc.detail,
            "code": exc.status_code,
            "path": str(request.url.path)
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=resp.model_dump()
    )

# General Exception Handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    resp = ErrorResponse.from_exception(exc, code=HTTPStatus.INTERNAL_SERVER_ERROR.value)
    if isinstance(resp.data, dict):
        resp.data["path"] = str(request.url.path)
    return JSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
        content=resp.model_dump()
    )

# Exécution directe pour dev
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="localhost", port=8000, reload=True)
