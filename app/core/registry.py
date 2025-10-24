from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union
from fastapi import FastAPI, APIRouter
from enum import Enum

from app.schemas.error_schema import ErrorResponse

class RouterItem:
    def __init__(
        self,
        router: APIRouter,
        prefix: str,
        tags: Optional[List[Union[str, Enum]]] = None,
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None
    ):
        self.router = router
        self.prefix = prefix
        self.tags = tags
        self.responses = responses or {}

        for code in [HTTPStatus.BAD_REQUEST, HTTPStatus.NOT_FOUND, HTTPStatus.INTERNAL_SERVER_ERROR]:
            if code.value not in self.responses:
                example = ErrorResponse(
                    isOk=False,
                    result=code.phrase,
                    data={
                        "detail": "Error message",
                        "code": code.value
                    }
                ).model_dump()

                self.responses[code.value] = {
                    "description": f"{code.value} {code.name.replace('_', ' ').title()}",
                    "content": {
                        "application/json": {
                            "example": example
                        }
                    }
                }

class RouterRegistry:
    def __init__(self):
        self.router_list: List[RouterItem] = []

    def register(
        self,
        router: APIRouter,
        prefix: str,
        tags: Optional[List[Union[str, Enum]]] = None,
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None
    ):
        item = RouterItem(router=router, prefix=prefix, tags=tags, responses=responses)
        self.router_list.append(item)

    def include_all(self, app: FastAPI):
        for item in self.router_list:
            app.include_router(
                item.router,
                prefix=item.prefix,
                tags=item.tags,
                responses=item.responses
            )
