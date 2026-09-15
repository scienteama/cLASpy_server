from app.schemas.user_schema import UserWithRecoveryCodes
from typing import Annotated, List
from fastapi import APIRouter, Body, Request
from app.core.provider import get_user_service
from app.schemas.response_schema import ApiResponse
from app.schemas.user_schema import UserIn, UserOut, UserUpdate
from fastapi import Depends
from app.services.users_service import UserService

router = APIRouter()


@router.post("/add-first", response_model=ApiResponse[UserWithRecoveryCodes])
async def register_first_user(
    req: Request,
    user_service: Annotated[UserService, Depends(get_user_service)],
    user: UserIn = Body(...),
):
    """
    Crée le premier utilisateur (admin) si aucun utilisateur n'existe.
    """
    new_user = await user_service.create_first_user(user)
    return ApiResponse[UserWithRecoveryCodes](data=new_user)


@router.post("/add", response_model=ApiResponse[UserWithRecoveryCodes])
async def register_user(
    req: Request,
    user_service: Annotated[UserService, Depends(get_user_service)],
    user: UserIn = Body(...),
):
    """
    Crée un nouvel utilisateur.
    """
    new_user = await user_service.create_user(user)
    return ApiResponse[UserWithRecoveryCodes](data=new_user)


@router.patch("/update/{user_id}", response_model=ApiResponse[UserOut])
async def update_user(
    user_id: int,
    user_service: Annotated[UserService, Depends(get_user_service)],
    fields: UserUpdate = Body(...),
):
    """
    Met à jour partiellement un utilisateur existant.
    """
    updated_user = await user_service.update_user_by_id(user_id, fields)
    return ApiResponse[UserOut](data=updated_user)


@router.delete("/delete/{user_id}", response_model=ApiResponse[str])
async def delete_user(
    user_id: int, user_service: Annotated[UserService, Depends(get_user_service)]
):
    """
    Supprime un utilisateur par ID.
    """
    result = await user_service.delete_user_by_id(user_id)
    return ApiResponse[str](data=result)


@router.get("/get-by-id/{user_id}", response_model=ApiResponse[UserOut])
async def get_user(user_id: int, user_service: Annotated[UserService, Depends(get_user_service)]):
    """
    Récupère un utilisateur par ID.
    """
    user = await user_service.get_user_by_id(user_id)
    return ApiResponse[UserOut](data=user)


@router.get("/get-by-email", response_model=ApiResponse[UserOut])
async def get_user_by_email(
    email: str, user_service: Annotated[UserService, Depends(get_user_service)]
):
    """
    Récupère un utilisateur par email.
    """
    user = await user_service.get_user_by_email(email)
    return ApiResponse[UserOut](data=user)


@router.get("/me", response_model=ApiResponse[UserOut])
async def get_me(
    req: Request, user_service: Annotated[UserService, Depends(get_user_service)]
) -> ApiResponse[UserOut]:
    """
    Récupère l'utilisateur courant.
    """
    user = await user_service.get_user_by_id(req.state.user.id)
    return ApiResponse[UserOut](data=user)


@router.get("/all", response_model=ApiResponse[List[UserOut]])
async def get_all_users(user_service: Annotated[UserService, Depends(get_user_service)]):
    """
    Récupère la liste complète des utilisateurs.
    """
    users = await user_service.get_all_users()
    return ApiResponse[List[UserOut]](data=users)


@router.get("/count", response_model=ApiResponse[int])
async def get_user_count(user_service: Annotated[UserService, Depends(get_user_service)]):
    """
    Récupère le nombre total d'utilisateurs.
    """
    count = await user_service.get_user_count()
    return ApiResponse[int](data=count)
