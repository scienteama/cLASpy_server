from typing import List

from fastapi import APIRouter
from app.core.tasks import cpu_history, ram_history
from app.schemas.response_schema import ApiResponse, MetricPoint

router = APIRouter()


@router.get("/cpu/history", response_model=ApiResponse[List[MetricPoint]])
def get_cpu_history():
    result = list(cpu_history)
    return ApiResponse[List[MetricPoint]](data=result)


@router.get("/memory/history", response_model=ApiResponse[List[MetricPoint]])
def get_memory_history():
    result = list(ram_history)
    return ApiResponse[List[MetricPoint]](data=result)
