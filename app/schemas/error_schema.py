from http import HTTPStatus
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
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
        jsonResponse =  JSONResponse(
            status_code=exc.status_code,
            content=resp.model_dump()
        )
        jsonResponse.headers["Access-Control-Allow-Origin"] = "https://localhost:8081"
        jsonResponse.headers["Access-Control-Allow-Credentials"] = "true"
        return jsonResponse
    
    @staticmethod
    def validation_exception_handler(request: Request, exc: RequestValidationError):
        response = ErrorResponse(
            isOk=False,
            result="Pydantic Validation Error",
            data={
                "detail": exc.errors(),
                "body": exc.body,
                "code": 422
            }
        )
        jsonResponse = JSONResponse(status_code=422, content=response.model_dump())
        jsonResponse.headers["Access-Control-Allow-Origin"] = "https://localhost:8081"
        jsonResponse.headers["Access-Control-Allow-Credentials"] = "true"
        return jsonResponse


    @staticmethod
    def generic_exception_handler(request: Request, exc: Exception):
        resp = ErrorResponse.from_exception(exc, code=HTTPStatus.INTERNAL_SERVER_ERROR.value)
        if isinstance(resp.data, dict):
            resp.data["path"] = str(request.url.path)
        jsonResponse =  JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
            content=resp.model_dump()
        )
        jsonResponse.headers["Access-Control-Allow-Origin"] = "https://localhost:8081"
        jsonResponse.headers["Access-Control-Allow-Credentials"] = "true"
        return jsonResponse