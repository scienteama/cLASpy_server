
from app.dao.user_dao import UserDAO
from app.models.user import User
from app.schemas.user_schema import UserCreate, UserResponse
from app.utils.auth_utils import hash_password

class UserService:
    """
    Service métier pour la gestion des utilisateurs.
    """
    def __init__(self, user_dao: UserDAO):
        self.user_dao = user_dao

    def create_user(self, user_create: UserCreate) -> UserResponse:
        hashed_password = hash_password(user_create.password)
        user = User(
            username=user_create.username,
            email=user_create.email,
            password=hashed_password
        )
        user = self.user_dao.create(user)
        return UserResponse.from_orm(user)

    def get_user_by_id(self, user_id: int) -> UserResponse | None:
        user = self.user_dao.get_by_id(user_id)
        return UserResponse.from_orm(user) if user else None

    def get_user_by_email(self, email: str) -> UserResponse | None:
        user = self.user_dao.get_by_email(email)
        return UserResponse.from_orm(user) if user else None
