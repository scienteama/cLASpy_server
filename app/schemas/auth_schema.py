from typing import Any
from fastapi import Response
from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: int
    email: str
    role_id: int = Field(..., alias="roleId")


class AuthResponse(BaseModel):
    isAuthenticated: bool
    exp: int
    sessionUserData: TokenData | None = None


class CookieConfig(BaseModel):
    key: str
    value: Any
    http_only: bool = True
    secure: bool = True
    samesite: str = "None"
    max_age_minutes: int

    @property
    def max_age(self) -> int:
        """Retourne max_age en secondes pour set_cookie."""
        return self.max_age_minutes * 60


def set_http_only_cookie(res: Response, config: CookieConfig):
    if config:
        res.set_cookie(
            key=config.key,
            value=config.value,
            httponly=config.http_only,
            secure=config.secure,
            samesite=config.samesite,
            max_age=config.max_age,
        )
