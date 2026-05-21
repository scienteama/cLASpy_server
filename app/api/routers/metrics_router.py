import os
from typing import List

from fastapi import APIRouter
import psutil
from app.core.tasks import cpu_history, ram_history
from app.schemas.response_schema import ApiResponse, DiskInfo, MetricPoint

router = APIRouter()


@router.get("/cpu/history", response_model=ApiResponse[List[MetricPoint]])
def get_cpu_history():
    result = list(cpu_history)
    return ApiResponse[List[MetricPoint]](data=result)

@router.get("/disk/infos", response_model=ApiResponse[DiskInfo])
def get_disk_infos():
    disk_path = os.path.abspath(os.sep)
    disk_usage = psutil.disk_usage(disk_path)
    result = DiskInfo(
        total=disk_usage.total,
        used=disk_usage.used,
        free=disk_usage.free,
        percent=disk_usage.percent
    )
    return ApiResponse[DiskInfo](data=result)


@router.get("/memory/history", response_model=ApiResponse[List[MetricPoint]])
def get_memory_history():
    result = list(ram_history)
    return ApiResponse[List[MetricPoint]](data=result)
