from functools import wraps
from sqlalchemy.exc import DBAPIError
from fastapi import HTTPException
from http import HTTPStatus


def catch_db_errors(message_model: str = ""):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = "Une erreur interne est survenue."
            try:
                return await func(*args, **kwargs)
            except DBAPIError as e:
                db = getattr(args[0], "db", None)
                if db:
                    await db.rollback()
                msg = str(e.orig)

                if message_model:
                    result = message_model

                if "DETAIL:" in msg:
                    result = result + f" : {msg.split('DETAIL:')[1].strip()}"

                raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=result)
            except Exception:
                raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=result)

        return wrapper

    return decorator
