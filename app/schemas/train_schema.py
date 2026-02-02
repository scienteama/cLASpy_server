from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, RootModel

from app.schemas.sklearn_schema import AlgoParamsResponse


class PointCloudInfo(BaseModel):
    file_name: str = Field(..., alias="name")
    file_type: Literal['.csv', '.las'] = Field(..., alias="type")
    points_number: int = Field(..., alias="pointsNumber")
    las_version: Optional[float] = Field(None, alias="lasVersion")
    las_point_format: Optional[int] = Field(None, alias="lasPointFormat")
    feat_list: Optional[List[str]] = Field(None, alias="featuresList")

    class Config:
        validate_by_name = True

class TrainParameters(BaseModel):
    file_id: str = Field(..., alias="fileId")
    input_data: Optional[str] = None
    folder_id: str = Field(..., alias="folderId")
    output: Optional[str] = None
    created_at: datetime = Field(..., alias="createdAt")
    samples: float
    train_r: float = Field(..., alias="trainingRatio")
    scaler: str
    scoring: str = Field(..., alias="scorer")
    n_jobs: int = Field(..., alias="nJobsCv")
    pca: int
    random_state: int = Field(..., alias="randomState")
    algo: Optional[str] = None
    algorithm: Optional[str] = None
    png_features: bool = Field(..., alias="pngFeatures")
    parameters: Optional[Dict[str, Any]] = None
    features: List[str] = Field(..., alias="featureNames")
    fillnan: str
    config: Optional[Any] = None
    grid_search: bool = False
    param_grid: Any = None

    class Config:
        validate_by_name = True


