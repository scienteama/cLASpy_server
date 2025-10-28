from typing import Any
from fastapi import Response
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: int
    email: str

# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class CookieConfig(BaseModel):
    key: str
    value: Any
    http_only: bool = True
    secure: bool = True
    samesite: str = "lax"
    max_age_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES

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
            max_age=config.max_age)