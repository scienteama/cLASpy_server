from typing import List, Optional
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notifications import Notification
from app.models.user import User
from app.schemas.notification_schema import NotificationType


class NotificationDAO:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, notification: Notification) -> Notification:
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    async def add_for_all(
        self,
        message: str,
        notif_type: NotificationType,
        sender_id: int | None = None,
    ) -> int:

        result = await self.db.execute(select(User.id))
        user_ids = result.scalars().all()

        notifications = [
            Notification(
                user_id=user_id,
                sender_id=sender_id,
                type=notif_type,
                message=message,
            )
            for user_id in user_ids
        ]

        self.db.add_all(notifications)
        await self.db.commit()

        return len(notifications)

    async def get_by_id(self, notification_id: int) -> Optional[Notification]:
        result = await self.db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: int) -> List[Notification]:
        result = await self.db.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        )
        return result.scalars().all()

    async def get_all(self) -> List[Notification]:
        result = await self.db.execute(
            select(Notification).order_by(Notification.created_at.desc())
        )
        return result.scalars().all()

    async def count_unread_by_user(self, user_id: int) -> int:
        result = await self.db.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id, Notification.is_read.is_(False)
            )
        )
        return result.scalar() or 0

    async def mark_as_read(self, notification_id: int) -> None:
        await self.db.execute(
            update(Notification).where(Notification.id == notification_id).values(is_read=True)
        )
        await self.db.commit()

    async def mark_all_as_read(self, user_id: int) -> int:
        result = await self.db.execute(
            update(Notification).where(Notification.user_id == user_id).values(is_read=True)
        )
        updated_count = result.rowcount
        await self.db.commit()

        return updated_count

    async def delete(self, notification_id: int) -> bool:
        result = await self.db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one_or_none()

        if not notification:
            return False

        await self.db.delete(notification)
        await self.db.commit()
        return True

    async def delete_all_by_user(self, user_id: int) -> int:
        result = await self.db.execute(select(Notification).where(Notification.user_id == user_id))
        notifications = result.scalars().all()
        count = len(notifications)

        if count > 0:
            await self.db.execute(
                Notification.__table__.delete().where(Notification.user_id == user_id)
            )
            await self.db.commit()

        return count
