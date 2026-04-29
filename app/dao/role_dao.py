from http import HTTPStatus
from typing import Any, Dict, List
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.role import Role
from app.utils.db_error import catch_db_errors


class RoleDAO:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, role_id: int) -> Role:
        result = await self.db.execute(select(Role).where(Role.id == role_id))
        role: Role | None = result.scalar_one_or_none()
        if not role:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Role {role_id} introuvable"
            )
        return role

    async def get_by_name(self, name: str) -> Role:
        result = await self.db.execute(select(Role).where(Role.name == name))
        role: Role | None = result.scalar_one_or_none()
        return role

    async def get_all(self) -> List[Role]:
        result = await self.db.execute(select(Role))
        roles: List[Role] = result.scalars().all()
        return roles

    @catch_db_errors(message_model="Erreur lors de la mise à jour du rôle")
    async def update_role(self, role_id: int, update_data: Dict[str, Any]) -> Role:
        result = await self.db.execute(select(Role).where(Role.id == role_id))
        role: Role | None = result.scalar_one_or_none()
        if not role:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Rôle introuvable"
            )

        for field, value in update_data.items():
            setattr(role, field, value)

        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return role
