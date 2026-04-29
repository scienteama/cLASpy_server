from http import HTTPStatus
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from app.core.provider import get_file_service, get_ws_service
from app.schemas.response_schema import ApiResponse
from app.services.files_service import FileService
from app.services.ws_service import SocketIOService

router = APIRouter()


@router.post("/celery", response_model=ApiResponse[str])
async def train_task_celery_event(
    event: dict[str, Any],
    file_service: Annotated[FileService, Depends(get_file_service)],
    ws_service: Annotated[SocketIOService, Depends(get_ws_service)]
):
    result = event.get("result", {})
    if not result:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Payload missing result field"
        )

    user = result.get("user")
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="User information missing in result payload"
        )

    user_id = user.get("user_id")
    role_id = user.get("role_id")

    if not user_id or not role_id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="User information missing or invalid"
        )

    files_list = result.get("files", [])
    parent_id = result.get("parent_id", "root")
    task_id = result.get("task_id", "unknown")

    files_dict = {
        f"file_{i+1}": Path(f)
        for i, f in enumerate(files_list)
    }

    try:
        res = await file_service.save_ml_result(
            files_dict,
            user_id,
            role_id,
            parent_id
        )

        await ws_service.send_to_user(
            user_id,
            "ml_task_done",
            {
                "task_id": task_id,
                "result": res
            }
        )

        return ApiResponse[str](
            result="Files processed and saved successfully"
        )

    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Error processing files: {str(e)}"
        )
