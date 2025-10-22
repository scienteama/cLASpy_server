from fastapi import APIRouter, HTTPException
from app.schemas.user_schema import UserCreate, UserResponse
from app.core.service_provider import ServiceProvider

router = APIRouter()
UserService = ServiceProvider.get_user_service()

@router.post("/users", response_model=UserResponse)
async def register_user(user: UserCreate):
    db_user = await UserService.create_user(user)
    if db_user is None:
        raise HTTPException(status_code=400, detail="User already exists")
    return db_user

@router.get("/users/{user_id}", response_model=UserResponse)
async def read_user(user_id: int):
    db_user = await UserService.get_user_by_id(user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user