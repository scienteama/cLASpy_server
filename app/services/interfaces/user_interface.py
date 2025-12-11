from typing import Protocol, List
from app.schemas.user_schema import UserBase, UserIn, UserOut, UserUpdate
from sqlalchemy.ext.asyncio import AsyncSession

class IUserService(Protocol):
    async def create_user(self, user: UserIn, db: AsyncSession) -> UserOut:
        ...

    async def update_user_by_id(self, user_id: int, fields: UserUpdate, db: AsyncSession) -> UserOut:
        ...

    async def delete_user_by_id(self, user_id: int, db: AsyncSession) -> str:
        ...

    async def get_user_by_id(self, user_id: int, db: AsyncSession) -> UserOut:
        ...

    async def get_user_by_email(self, email: str, db: AsyncSession) -> UserOut:
        ...

    async def get_full_user_by_email(self, email: str, db: AsyncSession) -> UserBase:
        ...

    async def get_all_users(self, db: AsyncSession) -> List[UserOut]:
        ...

    async def user_is_admin(self, user_id: int, db: AsyncSession) -> bool:
        ...
