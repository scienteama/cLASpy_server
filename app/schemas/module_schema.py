from typing import List, Optional
from pydantic import BaseModel

class ClaspyModule(BaseModel):
    name: str
    version: Optional[str]
    enable: bool
    description: Optional[str]
    tooltip: Optional[str]

class Worker(BaseModel):
    name: str
    pid: int

class CeleryWorker(BaseModel):
    enabled: bool
    workers: List[Worker] = []