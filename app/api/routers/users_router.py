from typing import List
from fastapi import APIRouter, Body, Request
from app.schemas.response_schema import ApiResponse
from app.schemas.user_schema import UserIn, UserOut, UserUpdate
from app.core.service_provider import ServiceProvider
from fastapi import Depends
from app.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
user_service = ServiceProvider.get_user_service()

@router.post("/add", response_model=ApiResponse[UserOut])
async def register_user(req: Request, user: UserIn = Body(...), db: AsyncSession = Depends(get_async_db)):
    """
    Crée un nouvel utilisateur.
    """
    new_user = await user_service.create_user(user, db)
    return ApiResponse[UserOut](data=new_user)

@router.patch("/update/{user_id}", response_model=ApiResponse[UserOut])
async def update_user(user_id: int, fields: UserUpdate = Body(...), db: AsyncSession = Depends(get_async_db)):
    """
    Met à jour partiellement un utilisateur existant.
    """
    updated_user = await user_service.update_user_by_id(user_id, fields, db)
    return ApiResponse[UserOut](data=updated_user)

@router.delete("/delete/{user_id}", response_model=ApiResponse[str])
async def delete_user(user_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Supprime un utilisateur par ID.
    """
    result = await user_service.delete_user_by_id(user_id, db)
    return ApiResponse[str](data=result)

@router.get("/get-by-id/{user_id}", response_model=ApiResponse[UserOut])
async def get_user(user_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Récupère un utilisateur par ID.
    """
    user = await user_service.get_user_by_id(user_id, db)
    return ApiResponse[UserOut](data=user)

@router.get("/get-by-email", response_model=ApiResponse[UserOut])
async def get_user(email: str, db: AsyncSession = Depends(get_async_db)):
    """
    Récupère un utilisateur par email.
    """
    user = await user_service.get_user_by_email(email, db)
    return ApiResponse[UserOut](data=user)

@router.get("/me", response_model=ApiResponse[UserOut])
async def get_me(req: Request, db: AsyncSession = Depends(get_async_db)) -> ApiResponse[UserOut]:
    """
    Récupère l'utilisateur courant.
    """
    user = await user_service.get_user_by_id(req.state.user.id, db)
    return ApiResponse[UserOut](data=user)

@router.get("/all", response_model=ApiResponse[List[UserOut]])
async def get_all_users(db: AsyncSession = Depends(get_async_db)):
    """
    Récupère la liste complète des utilisateurs.
    """
    users = await user_service.get_all_users(db)
    return ApiResponse[List[UserOut]](data=users)