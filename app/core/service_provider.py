from app.services.auth_service import AuthService
from app.services.claspy_ml_service import ClaspyMLService
from app.services.files_service import FileService
from app.services.modules_service import ModulesService
from app.services.users_service import UserService
from app.dao.user_dao import UserDAO

class ServiceProvider:
    """
    Conteneur global d'injection des services.
    """
    _file_service: FileService | None = None
    _user_service: UserService | None = None
    _modules_service: ModulesService | None = None
    _claspy_ML_service: ClaspyMLService | None = None
    _auth_service: AuthService | None = None

    @classmethod
    def get_file_service(cls) -> FileService:
        if cls._file_service is None:
            cls._file_service = FileService(upload_dir="uploads")
        return cls._file_service

    @classmethod
    def get_user_service(cls) -> UserService:
        if cls._user_service is None:
            cls._user_service = UserService(UserDAO)
        return cls._user_service
    
    @classmethod
    def get_auth_service(cls) -> AuthService:
        if cls._auth_service is None:
            cls._auth_service = AuthService(cls.get_user_service())
        return cls._auth_service
    
    
    @classmethod
    def get_modules_service(cls) -> ModulesService:
        if cls._modules_service is None:
            cls._modules_service = ModulesService()
        return cls._modules_service
    
    @classmethod
    def get_claspy_ML_service(cls) -> ClaspyMLService:
        if cls._claspy_ML_service is None:
            cls._claspy_ML_service = ClaspyMLService()
        return cls._claspy_ML_service
