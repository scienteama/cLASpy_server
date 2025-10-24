from typing import Annotated, Optional
from pydantic import BaseModel, EmailStr, Field, constr
from datetime import datetime

class User(BaseModel):
    id: int
    firstname: str
    lastname: str
    email: str
    password: str
    createdAt: datetime
    updatedAt: datetime
    lastLogin: datetime
    role_id: int

    class Config:
        from_attributes = True
        validate_by_name = True

class UserIn(BaseModel):
    firstname: Annotated[str, constr(min_length=1, max_length=50)]
    lastname: Annotated[str,constr(min_length=1, max_length=50)]
    email: EmailStr
    password: Annotated[str,constr(min_length=8, max_length=72)]
    role_id: int = Field(..., alias="roleId")
    lastLogin: Optional[datetime] = Field(None)

    class Config:
        validate_by_name = True

class UserOut(BaseModel):
    id: int
    firstname: str
    lastname: str
    email: EmailStr
    createdAt: datetime
    updatedAt: datetime
    lastLogin: Optional[datetime] = Field(None)
    role_id: int = Field(..., alias="roleId")

    class Config:
        from_attributes = True
        validate_by_name = True

class UserUpdate(BaseModel):
    firstname: Optional[Annotated[str, constr(min_length=1, max_length=50)]] = None
    lastname: Optional[Annotated[str, constr(min_length=1, max_length=50)]] = None
    email: Optional[EmailStr] = None
    password: Optional[Annotated[str, constr(min_length=8)]] = None
    role_id: Optional[int] = None
    lastLogin: Optional[datetime] = None
