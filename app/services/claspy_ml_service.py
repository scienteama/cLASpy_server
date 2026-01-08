import inspect
from typing import Any, List, Optional, Dict

try:
    import cLASpy_ML
    from cLASpy_ML import cLASpy_Classes
    import sklearn.ensemble as algorithms
    from app.utils.claspy_ml_utils import enrich_algorithm_params
except ModuleNotFoundError:
    cLASpy_ML = None
    cLASpy_Classes = None
    algorithms = None
    enrich_algorithm_params = None


class ClaspyMLService:
    """
    TODO : Renseigner la doc.
    """

    trainer: Optional[Any]

    def __init__(self):
        if cLASpy_ML is not None and cLASpy_Classes is not None:
            self.plugin = cLASpy_ML
            self.classes = cLASpy_Classes
            self.trainer = cLASpy_Classes.ClaspyTrainer
        else:
            self.plugin = None
            self.classes = None
            self.trainer = None

    def get_core_version(self) -> str:
        """
        Retourne la version du core du plugin cLASpy_ML.
        """
        if self.classes is not None:
            return f"core_version : {self.classes.cLASpy_Core_version}"
        return "Plugin cLASpy_ML non chargé."

    def get_all_algorithms(self) -> List[str]:
        """
        Retourne la liste des algorithmes disponibles dans sklearn.ensemble.
        """
        if self.classes is None or algorithms is None:
            raise ModuleNotFoundError("Plugin cLASpy_ML non chargé.")

        algo_names = [
            name for name, obj in inspect.getmembers(algorithms, inspect.isclass)
            if not name.startswith("_")
        ]
        return algo_names

    def get_algorithm_parameters(self, name: str) -> Optional[Dict[str, dict]]:
        """
        Retourne les paramètres enrichis d'un algorithme sklearn.ensemble
        spécifié par son nom.
        """
        if self.classes is None or algorithms is None or enrich_algorithm_params is None:
            return None

        # Récupère la classe sklearn correspondante au nom
        algo_class = getattr(algorithms, name, None)
        if algo_class is None:
            raise ValueError(f"Algorithm '{name}' not found in sklearn.ensemble")

        # Instancie l'algorithme
        self.trainer = algo_class()

        # Retourne les paramètres enrichis
        return enrich_algorithm_params(self.trainer)
