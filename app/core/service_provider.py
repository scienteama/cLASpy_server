from app.dao.user_dao import UserDAO
from app.services.auth_service import AuthService
from app.services.claspy_ml_service import ClaspyMLService
from app.services.config_service import ConfigService
from app.services.files_service import FileService
from app.services.interfaces.auth_interface import IAuthService
from app.services.interfaces.claspyml_interface import IClaspyMLService
from app.services.interfaces.config_interface import IConfigService
from app.services.interfaces.files_interface import IFileService
from app.services.interfaces.module_interface import IModuleService
from app.services.interfaces.user_interface import IUserService
from app.services.modules_service import ModulesService
from app.services.users_service import UserService


class ServiceProvider:
    """
    Gestion des singletons de service avec typage via interfaces.
    """
    _auth_service: IAuthService | None = None
    _user_service: IUserService | None = None
    _file_service: IFileService | None = None
    _module_service: IModuleService | None = None
    _claspyml_service: IClaspyMLService | None = None
    _config_service: IConfigService | None = None

    @classmethod
    def init_services(cls):
        """
        Initialise les singletons dans le bon ordre.
        """
        cls._user_service = UserService()

        # Dépendances
        cls._file_service = FileService(cls._user_service)
        cls._auth_service = AuthService(cls._user_service)

        # Services indépendants
        cls._module_service = ModulesService()
        cls._claspyml_service = ClaspyMLService()
        cls._config_service = ConfigService()

    @classmethod
    def get_user_service(cls) -> IUserService:
        if cls._user_service is None:
            cls._user_service = UserService()
        return cls._user_service

    @classmethod
    def get_auth_service(cls) -> IAuthService:
        if cls._auth_service is None:
            cls._auth_service = AuthService(cls.get_user_service())
        return cls._auth_service

    @classmethod
    def get_file_service(cls) -> IFileService:
        if cls._file_service is None:
            cls._file_service = FileService(cls.get_user_service())
        return cls._file_service

    @classmethod
    def get_module_service(cls) -> IModuleService:
        if cls._module_service is None:
            cls._module_service = ModulesService()
        return cls._module_service

    @classmethod
    def get_claspyml_service(cls) -> IClaspyMLService:
        if cls._claspyml_service is None:
            cls._claspyml_service = ClaspyMLService()
        return cls._claspyml_service
    
    @classmethod
    def get_config_service(cls) -> IConfigService:
        if cls._config_service is None:
            cls._config_service = ConfigService()
        return cls._config_service
