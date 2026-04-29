from typing import Annotated, List
from fastapi import APIRouter, Body
from app.core.provider import get_role_service
from app.schemas.response_schema import ApiResponse
from app.schemas.role_schema import Role, RoleUpdate
from fastapi import Depends
from app.services.role_service import RoleService

router = APIRouter()


@router.get("/all", response_model=ApiResponse[List[Role]])
async def get_all(role_service: Annotated[RoleService, Depends(get_role_service)]):
    """
    Récupère la liste complète des rôles.
    """
    roles = await role_service.get_all_roles()
    return ApiResponse[List[Role]](data=roles)


@router.get("/get-by-id/{role_id}", response_model=ApiResponse[Role])
async def get_role_by_id(
    role_id: int, role_service: Annotated[RoleService, Depends(get_role_service)]
):
    """
    Récupère un rôle par son ID.
    """
    role = await role_service.get_role_by_id(role_id)
    return ApiResponse[Role](data=role)


@router.get("/get-by-email", response_model=ApiResponse[Role])
async def get_role_by_name(
    name: str, role_service: Annotated[RoleService, Depends(get_role_service)]
):
    """
    Récupère un rôle par son nom.
    """
    role = await role_service.get_role_by_name(name)
    return ApiResponse[Role](data=role)


@router.patch("/update/{role_id}", response_model=ApiResponse[Role])
async def update_user(
    role_id: int,
    role_service: Annotated[RoleService, Depends(get_role_service)],
    fields: RoleUpdate = Body(...),
):
    """
    Met à jour un rôle.
    """
    updated_role = await role_service.update_role_by_id(role_id, fields)
    return ApiResponse[Role](data=updated_role)
