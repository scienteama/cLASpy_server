from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import database
from app.api.users_router import router as users_router
from app.api.files_router import router as file_router
from app.api.modules_router import router as modules_router
from app.api.claspy_ml_router import router as claspy_ml_router

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="localhost", port=8000, reload=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code au démarrage
    await database.connect()
    yield
    # Code à l'arrêt
    await database.disconnect()

app = FastAPI(lifespan=lifespan, title="cLASpy_T Web API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en prod, remplacer "*" par vrai domaine
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routes
app.include_router(file_router, prefix="/api/files", tags=["Files"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(modules_router, prefix="/api/modules", tags=["Modules"])
app.include_router(claspy_ml_router, prefix="/api/claspy_ml", tags=["Claspy_ML"])



