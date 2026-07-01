from typing import Optional
from app.services.ws_service import SocketIOService
from app.dao.notif_dao import NotificationDAO
from app.models.notifications import Notification
from app.schemas.notification_schema import NotificationBase, NotificationType


class NotificationService:

    def __init__(self, dao: NotificationDAO, ws_service: Optional[SocketIOService] = None):
        self.dao = dao
        self.ws_service = ws_service

    async def create_notification(
        self,
        user_id: int,
        message: str,
        notif_type: NotificationType,
        sender_id: Optional[int] = None,
    ) -> NotificationBase:

        notification = Notification(
            user_id=user_id,
            sender_id=sender_id,
            type=notif_type,
            message=message,
        )

        saved = await self.dao.add(notification)

        result = NotificationBase.model_validate(saved)

        if self.ws_service:
            await self.ws_service.send_to_user(
                user_id,
                "notification",
                result.model_dump(by_alias=True),
            )

        return result

    async def create_notification_for_all_users(
        self,
        message: str,
        notif_type: NotificationType,
        sender_id: int | None = None,
    ) -> int:

        count = await self.dao.add_for_all(
            message,
            notif_type,
            sender_id,
        )

        if self.ws_service:
            await self.ws_service.send_all(
                "notification",
                {
                    "message": message,
                    "type": notif_type.value,
                },
            )

        return count

    async def get_user_notifications(self, user_id: int) -> list[NotificationBase]:

        notifications = await self.dao.get_by_user(user_id)

        return [NotificationBase.model_validate(n) for n in notifications]

    async def get_unread_count(self, user_id: int) -> int:

        return await self.dao.count_unread_by_user(user_id)

    async def mark_as_read(self, user_id: int, notification_id: int) -> NotificationBase | None:

        notif = await self.dao.get_by_id(notification_id)

        if notif is None:
            return None

        if notif.user_id != user_id:
            return None

        updated = await self.dao.mark_as_read(notification_id)

        if updated is None:
            return None

        result = NotificationBase.model_validate(updated)

        if self.ws_service:
            await self.ws_service.send_to_user(
                user_id,
                "notification_read",
                result.model_dump(by_alias=True),
            )

        return result

    async def mark_all_as_read(self, user_id: int) -> int:

        updated_count = await self.dao.mark_all_as_read(user_id)

        if self.ws_service and updated_count > 0:
            await self.ws_service.send_to_user(
                user_id,
                "notifications_all_read",
                {"count": updated_count},
            )

        return updated_count

    async def delete(self, user_id: int, notification_id: int) -> bool:

        notif = await self.dao.get_by_id(notification_id)

        if notif is None:
            return False

        if notif.user_id != user_id:
            return False

        deleted = await self.dao.delete(notification_id)

        if deleted and self.ws_service:
            await self.ws_service.send_to_user(
                user_id,
                "notification_deleted",
                {
                    "notificationId": notification_id,
                },
            )

        return deleted

    async def delete_all_for_user(self, user_id: int) -> int:

        deleted_count = await self.dao.delete_all_by_user(user_id)

        if self.ws_service and deleted_count > 0:
            await self.ws_service.send_to_user(
                user_id,
                "notifications_deleted_all",
                {"count": deleted_count},
            )

        return deleted_count
