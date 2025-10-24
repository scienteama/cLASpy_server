from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class Role(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


