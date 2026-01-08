from typing import Any, Dict, List, Protocol
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession


class IUserDAO(Protocol):

    async def create(self, user: User, db: AsyncSession) -> User:
        ...

    async def update(self, user_id: int, update_data: Dict[str, Any], db: AsyncSession) -> User:
        ...

    async def delete(self, user_id: int, db: AsyncSession) -> bool:
        ...

    async def get_by_id(self, user_id: int, db: AsyncSession) -> User:
        ...

    async def get_by_email(self, email: str, db: AsyncSession) -> User:
        ...

    async def get_all_users(self, db: AsyncSession) -> List[User]:
        ...
