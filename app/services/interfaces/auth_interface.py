from http import HTTPStatus
from typing import Protocol
from fastapi import HTTPException, Response
from app.schemas.auth_schema import Token, TokenData
from app.schemas.user_schema import UserOut
from sqlalchemy.ext.asyncio import AsyncSession


class IAuthService(Protocol):
    """
    Interface pour le service AuthService.
    """

    async def authenticate(self, email: str, password: str, db: AsyncSession) -> UserOut:
        """Authentifie un utilisateur avec email et mot de passe."""

    async def create_access_token(self, user: UserOut) -> Token:
        """Crée un JWT pour un utilisateur donné."""

    async def clear_auth_cookie(self, res: Response, key: str) -> str:
        """Supprime le cookie d'authentification."""

    def verify_token(self, token: str) -> TokenData:
        """Vérifie un JWT et retourne les informations de l'utilisateur."""
