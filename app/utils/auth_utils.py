from datetime import datetime, timezone
from http import HTTPStatus
import os
from fastapi import HTTPException
import jwt
from pwdlib import PasswordHash
from app.core.config import get_settings
from app.schemas.auth_schema import TokenData


def hash_password(password: str) -> str:
    """Hash a password using pwdlib."""
    if not password:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Paramètres invalides"
        )
    password_hash = PasswordHash.recommended()
    salt = os.urandom(16)
    return password_hash.hash(password, salt=salt)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a hashed password against a plain password."""
    if not plain_password:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Paramètres invalides"
        )
    password_hash = PasswordHash.recommended()
    return password_hash.verify(plain_password, hashed_password)


def verify_token(token: str) -> TokenData:
    """
    Vérifie et décode un JWT Token et retourne les informations utiles.
    """
    try:

        config = get_settings()
        payload = jwt.decode(
            token,
            config.SECRET_KEY,
            algorithms=[config.ALGORITHM],
            options={"require": ["exp"]}
        )
        user = payload.get("user")
        if not user:
            raise_auth_exception("Email ou mot de passe incorrect")
        return TokenData(id=user["id"], email=user["email"], role_id=user["role_id"])
    except jwt.ExpiredSignatureError:
        raise_auth_exception("Session utilisateur expirée")
    except jwt.InvalidTokenError:
        raise_auth_exception("Token invalide")


def raise_auth_exception(detail: str):
    """Raise a standardized auth-related HTTPException with Bearer auth header."""
    raise HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},)
