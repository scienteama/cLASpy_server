from datetime import datetime, timedelta, timezone
from fastapi import Response
import jwt
from app.core.config import get_settings
from app.schemas.auth_schema import Token, TokenData
from app.schemas.user_schema import UserOut
from app.services.users_service import UserService
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.auth_utils import raise_auth_exception, verify_password

class AuthService:
    """
    Service de gestion d'authentification.
    """

    def __init__(self, user_service: UserService):
        self.user_service = user_service
        self.config = get_settings()
        
    async def authenticate(self, email: str, password: str, db: AsyncSession) -> UserOut:
        user = await self.user_service.get_full_user_by_email(email, db)
        if verify_password(password, user.password):
            return UserOut.model_validate(user) 
        else :None

    async def create_access_token(self, user: UserOut) -> Token:
        to_encode = {"user": TokenData(id=user.id, email=user.email).model_dump()}
        try:
            expire_minutes = max(int(self.config.ACCESS_TOKEN_EXPIRE_MINUTES), 1)
            print(expire_minutes)
        except (TypeError, ValueError):
            print ('value error')
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
            return TokenData(id=user["id"], email=user["email"])
        except jwt.ExpiredSignatureError:
            raise_auth_exception("Session utilisateur expirée")
        except jwt.InvalidTokenError:
            raise_auth_exception("Token invalide")
    
