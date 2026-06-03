from datetime import datetime, timezone
from typing import Generic, Optional, TypeVar
from pydantic import BaseModel, Field, field_serializer
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


class UTCBaseModel(BaseModel):

    @field_serializer(
        "created_at",
        "modified_at",
        "updated_at",
        "last_login",
        check_fields=False,
    )
    def _serialize_dt(self, dt: datetime | None):
        if dt is None:
            return None

        if dt.tzinfo is None:
            # SQLite returns naive datetimes, assume UTC
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class MetricPoint(BaseModel):
    t: float
    v: float


class DiskInfo(BaseModel):
    total: int
    used: int
    free: int
    percent: float
