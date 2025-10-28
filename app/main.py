from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from app.api.middlewares.auth_middleware import AuthMiddleware
from app.api.middlewares.cors_middleware import CORSMiddleware
from app.api.middlewares.utils_middleware import UtilsMiddleware
from app.core.registry import RouterRegistry
from app.database import engine
from app.api.routers.users_router import router as users_router
from app.api.routers.files_router import router as file_router
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

# App FastAPI
app = FastAPI(lifespan=lifespan, title="cLASpy_T Web API")

# Middlewares
app.add_middleware(CORSMiddleware)
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
app.add_exception_handler(Exception, ErrorResponse.generic_exception_handler)

# Exécution directe pour dev
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="localhost", port=8000, reload=True)
