from http import HTTPStatus

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.schemas.response_schema import ApiResponse

class ErrorResponse(ApiResponse[dict]):

    isOk: bool = False

    @classmethod
    def from_exception(cls, exc: Exception, code: int = HTTPStatus.INTERNAL_SERVER_ERROR.value):
        return cls(
            isOk=False,
            result=HTTPStatus(code).phrase,
            data={
                "detail": str(exc),
                "code": code,
            },
        )
    
    @staticmethod
    def http_exception_handler(request: Request, exc: HTTPException):
        resp = ErrorResponse(
            isOk=False,
            result=HTTPStatus(exc.status_code).phrase,
            data={
                "detail": exc.detail,
                "code": exc.status_code,
                "path": str(request.url.path)
            }
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=resp.model_dump()
        )


    @staticmethod
    def generic_exception_handler(request: Request, exc: Exception):
        resp = ErrorResponse.from_exception(exc, code=HTTPStatus.INTERNAL_SERVER_ERROR.value)
        if isinstance(resp.data, dict):
            resp.data["path"] = str(request.url.path)
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
            content=resp.model_dump()
        )

