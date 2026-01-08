from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from app.api.middlewares.auth_middleware import AuthMiddleware
from app.api.middlewares.utils_middleware import UtilsMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.registry import RouterRegistry
from app.core.service_provider import ServiceProvider
from app.database import engine
from app.api.routers.users_router import router as users_router
from app.api.routers.file_router import router as file_router
from app.api.routers.modules_router import router as modules_router
from app.api.routers.claspy_ml_router import router as claspy_ml_router
from app.api.routers.auth_router import router as auth_router
from app.schemas.error_schema import ErrorResponse

# Lifespan pour FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Création de la connexion à la DB au démarrage
    async with engine.begin() as conn:
        pass
    yield
    await engine.dispose()

config = get_settings()

# App FastAPI
app = FastAPI(lifespan=lifespan, title=config.app_name)


# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)
app.add_middleware(UtilsMiddleware)

# Enregistrement des routes
registry = RouterRegistry()
registry.register(auth_router, prefix="/api/auth", tags=["Authentification"])
registry.register(modules_router, prefix="/api/modules", tags=["Modules"])
registry.register(users_router, prefix="/api/users", tags=["Users"])
registry.register(file_router, prefix="/api/files", tags=["Files"])
registry.register(claspy_ml_router, prefix="/api/claspy_ml", tags=["Claspy_ML"])
registry.include_all(app)

# Exception Handlers
app.add_exception_handler(HTTPException, ErrorResponse.http_exception_handler)
app.add_exception_handler(RequestValidationError, ErrorResponse.validation_exception_handler)
app.add_exception_handler(Exception, ErrorResponse.generic_exception_handler)

ServiceProvider.init_services()

if __name__ == "__main__":
    import uvicorn
    from app.core.config import get_settings

    config = get_settings()

    use_https = config.ENV != "production"

    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=(config.ENV == "development"),
        ssl_keyfile=(config.PROJECT_ROOT / "certificats/claspy_key.pem" if use_https else None),
        ssl_certfile=(config.PROJECT_ROOT / "certificats/claspy_cert.pem" if use_https else None),
    )
