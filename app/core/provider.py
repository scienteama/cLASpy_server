from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.file_dao import FileDAO
from app.database import get_async_db
from app.dao.user_dao import UserDAO
from app.services.users_service import UserService
from app.services.auth_service import AuthService
from app.services.files_service import FileService
from app.services.modules_service import ModulesService
from app.services.claspy_ml_service import ClaspyMLService
from app.services.config_service import ConfigService


# ------------------------------------------------------------------
# DAO PROVIDERS
# ------------------------------------------------------------------

def get_user_dao(
    db: Annotated[AsyncSession, Depends(get_async_db)],
) -> UserDAO:
    return UserDAO(db)


def get_file_dao(
    db: Annotated[AsyncSession, Depends(get_async_db)],
) -> FileDAO:
    return FileDAO(db)

# ------------------------------------------------------------------
# DEPENDENCIES SERVICES
# ------------------------------------------------------------------


def get_user_service(
    user_dao: Annotated[UserDAO, Depends(get_user_dao)],
) -> UserService:
    return UserService(user_dao)


def get_auth_service(
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> AuthService:
    return AuthService(user_service)


def get_file_service(
    file_dao: Annotated[FileDAO, Depends(get_file_dao)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> FileService:
    return FileService(user_service, file_dao)


def get_claspyml_service(
    file_service: Annotated[FileService, Depends(get_file_service)],
) -> ClaspyMLService:
    return ClaspyMLService(file_service)

# ------------------------------------------------------------------
# NO DEPENDENCIES SERVICES
# ------------------------------------------------------------------


_module_service = ModulesService()
_config_service = ConfigService()


def get_module_service() -> ModulesService:
    return _module_service


def get_config_service() -> ConfigService:
    return _config_service
