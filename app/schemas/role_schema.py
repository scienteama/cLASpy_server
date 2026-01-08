from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class Role(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime


class UserRole(int, Enum):
    admin = 1
    poweruser = 2
    user = 3
    viewer = 4
