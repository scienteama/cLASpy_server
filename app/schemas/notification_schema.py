from datetime import datetime
from enum import StrEnum
from typing import Optional
from pydantic import Field
from app.schemas.response_schema import UTCBaseModel


class NotificationType(StrEnum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"

    USER_MESSAGE = "user_message"
    SYSTEM = "system"
    PLUGIN = "plugin"

    ML_TRAINING = "ml_training"
    ML_PREDICTION = "ml_prediction"
    ML_SEGMENTATION = "ml_segmentation"
    ML_FEATURES = "ml_features"

    FILE_UPLOAD = "file_upload"
    FILE_DELETE = "file_delete"


class NotificationBase(UTCBaseModel):
    id: int
    user_id: int = Field(..., alias="userId")
    sender_id: Optional[int] = Field(None, alias="senderId")
    type: NotificationType
    message: str
    is_read: bool = Field(False, alias="isRead")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    class Config:
        from_attributes = True
        validate_by_name = True
