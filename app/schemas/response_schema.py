from typing import Generic, Optional, TypeVar
from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

T = TypeVar("T")


class ApiResponse(GenericModel, Generic[T]):
    """
    Schéma de réponse API générique.
    """

    isOk: bool = Field(True, description="Statut de la réponse ('isOk = True', 'isOk = False')")
    result: str = Field("Success", description="Message principal de la réponse")
    data: Optional[T] = Field(None, description="Contenu additionnel ou résultat de la requête")

    class Config:
        json_schema_extra = {"example": {"result": "Opération réussie", "data": {}, "isOk": "True"}}


class MetricPoint(BaseModel):
    t: float
    v: float


class DiskInfo(BaseModel):
    total: int
    used: int
    free: int
    percent: float