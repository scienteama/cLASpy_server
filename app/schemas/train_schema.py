from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class PointCloudInfo(BaseModel):
    file_name: str = Field(..., alias="name")
    file_type: Literal['.csv', '.las'] = Field(..., alias="type")
    points_number: int = Field(..., alias="pointsNumber")
    las_version: Optional[float] = Field(None, alias="lasVersion")
    las_point_format: Optional[int] = Field(None, alias="lasPointFormat")
    feat_list: Optional[List[str]] = Field(None, alias="featuresList")

    class Config:
        validate_by_name = True
