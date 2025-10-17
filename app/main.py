from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.files_router import router as file_router

app = FastAPI(title="cLASpy_T Web API")

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


