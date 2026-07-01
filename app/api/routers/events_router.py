from fastapi import Request
from http import HTTPStatus
from pathlib import Path
from typing import Annotated, Any, List

from fastapi import APIRouter, Depends, HTTPException

from app.core.provider import get_file_service, get_notification_service, get_ws_service
from app.schemas.notification_schema import NotificationBase
from app.schemas.response_schema import ApiResponse
from app.services.files_service import FileService
from app.services.notifications_service import NotificationService
from app.services.ws_service import SocketIOService

router = APIRouter()


@router.get("/notifications/user/{user_id}", response_model=ApiResponse[List[NotificationBase]])
async def get_user_notifications(
    req: Request,
    user_id: int,
    notif_service: Annotated[NotificationService, Depends(get_notification_service)],
):
    user_id = int(req.state.user.id)
    if user_id != user_id:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Not authorized")

    notifications = await notif_service.get_user_notifications(user_id)
    return ApiResponse[List[NotificationBase]](data=notifications)


@router.get("/notifications/unread-count/{user_id}", response_model=ApiResponse[int])
async def get_unread_notification_count(
    req: Request,
    user_id: int,
    notif_service: Annotated[NotificationService, Depends(get_notification_service)],
):
    user_id = int(req.state.user.id)
    if user_id != user_id:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Not authorized")

    count = await notif_service.get_unread_count(user_id)
    return ApiResponse[int](data=count)


@router.patch("/notifications/mark-as-read/{notification_id}", response_model=ApiResponse[str])
async def mark_notification_as_read(
    req: Request,
    notification_id: int,
    notif_service: Annotated[NotificationService, Depends(get_notification_service)],
):
    user_id = int(req.state.user.id)
    if user_id != user_id:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Not authorized")

    await notif_service.mark_as_read(user_id, notification_id)
    return ApiResponse[str](result="Notification marked as read")


@router.patch("/notifications/mark-all-as-read/{user_id}", response_model=ApiResponse[str])
async def mark_all_notifications_as_read(
    req: Request,
    user_id: int,
    notif_service: Annotated[NotificationService, Depends(get_notification_service)],
):
    user_id = int(req.state.user.id)
    if user_id != user_id:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Not authorized")

    await notif_service.mark_all_as_read(user_id)
    return ApiResponse[str](result="All notifications marked as read")


@router.delete("/notifications/delete/{notification_id}", response_model=ApiResponse[str])
async def delete_notification(
    req: Request,
    notification_id: int,
    notif_service: Annotated[NotificationService, Depends(get_notification_service)],
):
    user_id = int(req.state.user.id)
    if user_id != user_id:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Not authorized")

    deleted = await notif_service.delete(user_id, notification_id)

    if not deleted:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Notification not found")
    return ApiResponse[str](result="Notification deleted")


@router.delete("/notifications/delete-all/{user_id}", response_model=ApiResponse[str])
async def delete_all_notifications_for_user(
    req: Request,
    user_id: int,
    notif_service: Annotated[NotificationService, Depends(get_notification_service)],
):
    user_id = int(req.state.user.id)
    if user_id != user_id:
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Not authorized")

    deleted = await notif_service.delete_all_for_user(user_id)
    return ApiResponse[str](result=f"{deleted} notifications deleted")


@router.post("/celery", response_model=ApiResponse[str])
async def train_task_celery_event(
    event: dict[str, Any],
    file_service: Annotated[FileService, Depends(get_file_service)],
    ws_service: Annotated[SocketIOService, Depends(get_ws_service)],
):
    result = event.get("result", {})
    if not result:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Payload missing result field"
        )

    user = result.get("user")
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="User information missing in result payload"
        )

    user_id = user.get("user_id")
    role_id = user.get("role_id")

    if not user_id or not role_id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="User information missing or invalid"
        )

    files_list = result.get("files", [])
    parent_id = result.get("parent_id", "root")
    task_id = result.get("task_id", "unknown")

    files_dict = {f"file_{i+1}": Path(f) for i, f in enumerate(files_list)}

    try:
        res = await file_service.save_ml_result(files_dict, user_id, role_id, parent_id)

        await ws_service.send_to_user(user_id, "ml_task_done", {"task_id": task_id, "result": res})

        return ApiResponse[str](result="Files processed and saved successfully")

    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f"Error processing files: {str(e)}"
        )
