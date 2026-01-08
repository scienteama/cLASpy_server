from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from fastapi import HTTPException, Response
import jwt
from app.core.config import get_settings
from app.schemas.auth_schema import Token, TokenData
from app.schemas.user_schema import UserOut, UserUpdate
from app.services.interfaces.user_interface import IUserService
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.auth_utils import raise_auth_exception, verify_password

class AuthService:
    """
    Service de gestion d'authentification.
    """

    def __init__(self, user_service: IUserService):
        self.user_service = user_service
        self.config = get_settings()
        
    async def authenticate(self, email: str, password: str, db: AsyncSession) -> UserOut:
        user = await self.user_service.get_full_user_by_email(email, db)
        if verify_password(password, user.password):
            await self.user_service.update_user_by_id(user.id, UserUpdate(last_login=datetime.now()), db)
            return UserOut.model_validate(user) 
        else :raise_auth_exception("Email ou mot de passe incorrect")

    async def create_access_token(self, user: UserOut) -> Token:
        to_encode = {"user": TokenData(id=user.id, email=user.email, role_id=user.role_id).model_dump()}
        try:
            expire_minutes = max(int(self.config.ACCESS_TOKEN_EXPIRE_MINUTES), 1)
        except (TypeError, ValueError):
            expire_minutes = 30
        expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
        to_encode["exp"] = expire
        encoded_jwt = jwt.encode(to_encode, self.config.SECRET_KEY, algorithm=self.config.ALGORITHM)
        return Token(access_token=encoded_jwt, token_type="bearer")
    
    async def clear_auth_cookie(self, res: Response, key: str) -> str:
        res.delete_cookie(key, httponly=True)
        return f"Déconnexion réussie"
    
    def verify_token(self, token: str) -> TokenData:
        """
        Vérifie et décode un JWT Token et retourne les informations utiles.
        """
        try:
            payload = jwt.decode(
                token,
                self.config.SECRET_KEY,
                algorithms=[self.config.ALGORITHM],
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
    
