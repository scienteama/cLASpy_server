from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, Field


class FileModel(BaseModel):
    id: str
    name: str
    type: str = "file"
    size_bytes: int
    created_at: datetime
    modified_at: datetime
    saved_as: Optional[str] = None
    mimeType: Optional[str] = None
    user_id: int


class FolderModel(BaseModel):
    id: str
    name: str
    type: str = "folder"
    size_bytes: int
    created_at: datetime
    modified_at: datetime
    depth: int
    user_id: int
    children: List[Union["FileModel", "FolderModel"]] = Field(default_factory=list)


# pour références récursives
FolderModel.model_rebuild()
