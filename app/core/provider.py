from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.file_dao import FileDAO
from app.dao.role_dao import RoleDAO
from app.database import get_async_db
from app.dao.user_dao import UserDAO
from app.services.role_service import RoleService
from app.services.users_service import UserService
from app.services.auth_service import AuthService
from app.services.files_service import FileService
from app.services.modules_service import ModulesService
from app.services.claspy_ml_service import ClaspyMLService
from app.services.config_service import ConfigService
from app.services.worker_service import WorkerService
from app.services.ws_service import SocketIOService

# ------------------------------------------------------------------
# DAO PROVIDERS
# ------------------------------------------------------------------


def get_user_dao(
    db: Annotated[AsyncSession, Depends(get_async_db)],
) -> UserDAO:
    return UserDAO(db)


def get_role_dao(
    db: Annotated[AsyncSession, Depends(get_async_db)],
) -> RoleDAO:
    return RoleDAO(db)


def get_file_dao(
    db: Annotated[AsyncSession, Depends(get_async_db)],
) -> FileDAO:
    return FileDAO(db)


# ------------------------------------------------------------------
# NO DEPENDENCIES SERVICES
# ------------------------------------------------------------------
_module_service = ModulesService()
_config_service = ConfigService()
_ws_service = SocketIOService()


def get_module_service() -> ModulesService:
    return _module_service


def get_config_service() -> ConfigService:
    return _config_service


def get_ws_service() -> SocketIOService:
    return _ws_service


# ------------------------------------------------------------------
# DEPENDENCIES SERVICES
# ------------------------------------------------------------------


def get_file_service(
    file_dao: Annotated[FileDAO, Depends(get_file_dao)],
    ws: Annotated[SocketIOService, Depends(get_ws_service)],
) -> FileService:
    return FileService(file_dao, ws)


def get_user_service(
    user_dao: Annotated[UserDAO, Depends(get_user_dao)],
    file_service: Annotated[FileService, Depends(get_file_service)],
) -> UserService:
    return UserService(user_dao, file_service)


def get_role_service(
    role_dao: Annotated[RoleDAO, Depends(get_role_dao)],
) -> RoleService:
    return RoleService(role_dao)


def get_auth_service(
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> AuthService:
    return AuthService(user_service)


def get_worker_service(
    m_service: Annotated[ModulesService, Depends(get_module_service)],
) -> WorkerService:
    return WorkerService(m_service)


def get_claspyml_service(
    file_service: Annotated[FileService, Depends(get_file_service)],
    m_service: Annotated[WorkerService, Depends(get_worker_service)],
    ws_service: Annotated[SocketIOService, Depends(get_ws_service)],
) -> ClaspyMLService:
    return ClaspyMLService(file_service, m_service, ws_service)
