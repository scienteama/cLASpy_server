from datetime import datetime, timedelta, timezone
from fastapi import Response
import jwt
from app.core.config import get_settings
from app.schemas.auth_schema import Token, TokenData
from app.schemas.user_schema import UserOut, UserUpdate
from app.services.users_service import UserService
from app.utils.auth_utils import raise_auth_exception, verify_password


class AuthService:
    """
    Service de gestion d'authentification.
    """

    def __init__(self, user_service: UserService):
        self.user_service = user_service
        self.config = get_settings()

    async def authenticate(self, email: str, password: str) -> UserOut:
        user = await self.user_service.get_full_user_by_email(email)
        if verify_password(password, user.password):
            await self.user_service.update_user_by_id(user.id, UserUpdate(last_login=datetime.now()))
            return UserOut.model_validate(user)
        else:
            raise_auth_exception("Email ou mot de passe incorrect")

    async def create_access_token(self, user: UserOut) -> Token:
        to_encode = {"user": TokenData(id=user.id, email=user.email, role_id=user.role_id).model_dump()}
        try:
            expire_minutes = max(int(self.config.ACCESS_TOKEN_EXPIRE_MINUTES), 1)
        except (TypeError, ValueError):
            expire_minutes = 30
        expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
        to_encode["exp"] = int(expire.timestamp())
        encoded_jwt = jwt.encode(to_encode, self.config.SECRET_KEY, algorithm=self.config.ALGORITHM)
        return Token(access_token=encoded_jwt, token_type="bearer")

    async def clear_auth_cookie(self, res: Response, key: str) -> str:
        res.delete_cookie(key, httponly=True)
        return f"Déconnexion réussie"
