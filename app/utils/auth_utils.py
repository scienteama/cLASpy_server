from http import HTTPStatus
import os
from fastapi import HTTPException, Response
from pwdlib import PasswordHash

from app.schemas.auth_schema import CookieConfig, Token

def hash_password(password: str) -> str:
    """Hash a password using pwdlib."""
    password_hash = PasswordHash.recommended()
    salt = os.urandom(16)
    return password_hash.hash(password, salt=salt)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a hashed password against a plain password."""
    password_hash = PasswordHash.recommended()
    return password_hash.verify(plain_password, hashed_password)

def raise_auth_exception(detail: str):
    """Raise a standardized auth-related HTTPException with Bearer auth header."""
    raise HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},)


