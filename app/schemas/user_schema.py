from typing import Annotated, Optional
from pydantic import BaseModel, EmailStr, Field, constr
from datetime import datetime
from app.schemas.response_schema import UTCBaseModel


class UserStorageDTO(UTCBaseModel):
    id: int
    user_id: int
    storage_used_bytes: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        validate_by_name = True


class UserBase(UTCBaseModel):
    id: int
    firstname: str
    lastname: str
    email: str
    password: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    role_id: int

    class Config:
        from_attributes = True
        validate_by_name = True


class UserIn(BaseModel):
    firstname: Annotated[str, constr(min_length=1, max_length=50)]
    lastname: Annotated[str, constr(min_length=1, max_length=50)]
    email: EmailStr
    password: Annotated[str, constr(min_length=8, max_length=72)]
    role_id: int

    class Config:
        validate_by_name = True


class UserOut(UTCBaseModel):
    id: int
    firstname: str
    lastname: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = Field(None)
    role_id: int
    storage: Optional[UserStorageDTO] = None

    class Config:
        from_attributes = True
        validate_by_name = True


class UserUpdate(BaseModel):
    firstname: Optional[Annotated[str, constr(min_length=1, max_length=50)]] = None
    lastname: Optional[Annotated[str, constr(min_length=1, max_length=50)]] = None
    email: Optional[EmailStr] = None
    password: Optional[Annotated[str, constr(min_length=8)]] = None
    role_id: Optional[int] = None
    last_login: Optional[datetime] = None


class RecoveryCodesResponse(BaseModel):
    warning: str
    formatted_codes: list[str]


class UserWithRecoveryCodes(UserOut):
    recovery_codes: RecoveryCodesResponse | None = None
