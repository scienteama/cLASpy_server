from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from app.schemas.response_schema import UTCBaseModel


class Role(UTCBaseModel):
    id: int
    name: str
    description: Optional[str]
    max_space: Optional[int] = Field(..., alias="maxSpace")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        validate_by_name = True


class RoleUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    max_space: Optional[int] = Field(..., alias="maxSpace")


class UserRole(int, Enum):
    admin = 1
    poweruser = 2
    user = 3
    viewer = 4
