from typing import Any, List, Optional, Dict
from pydantic import BaseModel, Field, RootModel

class AlgoParam(BaseModel):
    """Description détaillée d'un paramètre sklearn."""
    value: Any = Field(..., description="Valeur actuelle du paramètre")
    typeinfo: Optional[str] = Field(None, description="Type ou format du paramètre")
    choices: Optional[List[str]] = Field(None, description="Liste des valeurs possibles")
    default: Optional[str] = Field(None, description="Valeur par défaut")

class AlgoParamsResponse(RootModel[Dict[str, AlgoParam]]):
    """Retour complet des paramètres enrichis pour un algorithme sklearn."""
    pass