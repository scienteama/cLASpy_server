from typing import List, Optional, Dict


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
