from app.dao.interfaces.i_user_dao import IUserDAO
from app.dao.user_dao import UserDAO

class DAOProvider:

    _user_dao: IUserDAO | None = None

    @classmethod
    def get_user_dao(cls) -> IUserDAO:
        if cls._user_dao is None:
            cls._user_dao = UserDAO()
        return cls._user_dao

