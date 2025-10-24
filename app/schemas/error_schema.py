from http import HTTPStatus

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
