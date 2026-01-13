from pathlib import Path
from typing import List, Optional, Dict
from fastapi import UploadFile


class IClaspyMLService:

    def get_core_version(self) -> str:
        """Retourne la version du core du plugin cLASpy_ML."""
        ...

    def get_all_algorithms(self) -> List[str]:
        """Retourne la liste des algorithmes disponibles dans sklearn.ensemble."""
        ...

    def get_algorithm_parameters(self, name: str) -> Optional[Dict[str, dict]]:
        """Retourne les paramètres enrichis d'un algorithme sklearn.ensemble spécifié par son nom."""
        ...

    async def load_data_file(self, file: UploadFile | None = None, fileInfos: dict | None = None) -> str:
        """
        Charge un fichier .las ou .csv et retourne les infos du nuage de points.
        """
        ...
