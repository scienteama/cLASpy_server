import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
import socketio
from app.api.middlewares.auth_middleware import AuthMiddleware
from app.api.middlewares.utils_middleware import UtilsMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings, print_banner
from app.core.provider import get_ws_service
from app.core.registry import RouterRegistry
from app.core.tasks import metrics_loop
from app.database import engine
from app.api.routers.auth_router import router as auth_router
from app.api.routers.users_router import router as users_router
from app.api.routers.role_router import router as roles_router
from app.api.routers.file_router import router as file_router
from app.api.routers.modules_router import router as modules_router
from app.api.routers.claspy_ml_router import router as claspy_ml_router
from app.api.routers.config_router import router as config_router
from app.api.routers.events_router import router as events_router
from app.api.routers.metrics_router import router as metric_router
from app.schemas.error_schema import ErrorResponse


# Lifespan pour FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    # DB init
    async with engine.begin():
        pass

    # Socket.IO metrics task
    metrics_task = asyncio.create_task(metrics_loop(get_ws_service()))

    yield

    metrics_task.cancel()
    try:
        await metrics_task
    except asyncio.CancelledError:
        pass

    await engine.dispose()


config = get_settings()

# App FastAPI
app = FastAPI(lifespan=lifespan, title=config.app_name)

ws_service = get_ws_service()
ws_service.register_handlers()

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
registry.register(config_router, prefix="/api/settings", tags=["Settings"])
registry.register(modules_router, prefix="/api/modules", tags=["Modules"])
registry.register(users_router, prefix="/api/users", tags=["Users"])
registry.register(roles_router, prefix="/api/roles", tags=["Roles"])
registry.register(file_router, prefix="/api/files", tags=["Files"])
registry.register(claspy_ml_router, prefix="/api/claspy_ml", tags=["Claspy_ML"])
registry.register(events_router, prefix="/api/events", tags=["Events"])
registry.register(metric_router, prefix="/api/metrics", tags=["Metrics"])
registry.include_all(app)

# Exception Handlers
app.add_exception_handler(HTTPException, ErrorResponse.http_exception_handler)
app.add_exception_handler(RequestValidationError, ErrorResponse.validation_exception_handler)
app.add_exception_handler(Exception, ErrorResponse.generic_exception_handler)

socket_app = socketio.ASGIApp(ws_service.sio, app, socketio_path="socket.io")

if __name__ == "__main__":
    import uvicorn
    from app.core.config import get_settings

    print_banner()
    config = get_settings()

    use_https = config.ENV != "production"

    uvicorn.run(
        "app.main:socket_app",
        host=config.HOST,
        port=config.PORT,
        reload=(config.ENV == "development"),
        log_config=config.get_log_config(),
        log_level="debug" if config.ENV == "development" else "info",
        ssl_keyfile=(config.PROJECT_ROOT / "certificats/claspy_key.pem" if use_https else None),
        ssl_certfile=(config.PROJECT_ROOT / "certificats/claspy_cert.pem" if use_https else None),
    )
