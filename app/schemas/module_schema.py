from typing import Optional
from pydantic import BaseModel


class ClaspyModule(BaseModel):
    name: str
    version: Optional[str]
    enable: bool
    description: Optional[str]
    tooltip: Optional[str]
