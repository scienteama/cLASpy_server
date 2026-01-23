from typing import Any, List, Optional, Dict
from pydantic import BaseModel, Field, RootModel


class AlgoParam(BaseModel):
    """Description détaillée d'un paramètre sklearn."""
    value: Any = Field(..., description="Valeur actuelle du paramètre")
    typeinfo: Optional[str] = Field(None, description="Type ou format du paramètre")
    choices: Optional[List[str]] = Field(None, description="Liste des valeurs possibles")
    default: Optional[str] = Field(None, description="Valeur par défaut")


class AlgoParamsResponse(BaseModel):
    """Retour complet des paramètres enrichis pour un algorithme sklearn."""
    description: str = Field(..., description="Description générale de l'algorithme")
    parameters: Dict[str, AlgoParam] = Field(..., description="Paramètres enrichis")


class TrainArguments(BaseModel):
    input_data: str
    output: str
    algo: str

    config: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    features: Optional[List[str]] = None

    grid_search: bool = False
    param_grid: Optional[Dict[str, Any]] = None

    pca: Optional[int] = Field(None, ge=1)
    scaler: Optional[str] = None

    n_jobs: int = Field(1, ge=1)
    random_state: Optional[int] = None
    samples: Optional[int] = Field(None, gt=0)

    scoring: Optional[str] = None
    train_r: float = Field(0.8, gt=0, le=1)

    png_features: bool = False
