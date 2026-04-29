from typing import List
from app.dao.role_dao import RoleDAO
from app.schemas.role_schema import Role, RoleUpdate


class RoleService:
    """
    Service de gestion des rôles.
    """

    def __init__(self, role_dao: RoleDAO):
        self.roleDAO = role_dao

    # --- READ ---
    async def get_role_by_id(self, role_id: int) -> Role:
        """
        Récupère un rôle par son ID.
        """
        role = await self.roleDAO.get_by_id(role_id)
        return Role.model_validate(role)

    async def get_role_by_name(self, name: str) -> Role:
        """
        Récupère un rôle par son nom.
        """
        role = await self.roleDAO.get_by_name(name)
        return Role.model_validate(role)

    async def get_all_roles(self) -> List[Role]:
        """
        Retourne la liste complète des rôles.
        """
        roles = await self.roleDAO.get_all()
        return [Role.model_validate(u) for u in roles]

    # --- UPDATE ---

    async def update_role_by_id(self, role_id: int, fields: RoleUpdate) -> Role:
        """
        Met à jour un rôle.
        """
        await self.roleDAO.get_by_id(role_id)
        update_data = fields.model_dump(exclude_unset=True)

        updated_role = await self.roleDAO.update_role(role_id, update_data)
        return Role.model_validate(updated_role)
