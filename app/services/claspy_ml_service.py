from http import HTTPStatus
import inspect
import os
from pathlib import Path
import tempfile
from typing import Any, List, Optional, Dict
from fastapi import HTTPException, UploadFile

from app.core.config import Settings, get_settings
from app.schemas.sklearn_schema import TrainArguments

try:
    from cLASpy_ML import cLASpy_Classes
    from cLASpy_ML import cLASpy_T
    from cLASpy_ML.cLASpy_Classes import ClaspyTrainer, cLASpy_Core_version
    import sklearn.ensemble as algorithms
    from app.utils.claspy_ml_utils import enrich_algorithm_params
except ModuleNotFoundError as e:
    cLASpy_Classes = None
    algorithms = None
    enrich_algorithm_params = None
    print(f"Error: {e}")


class ClaspyMLService:
    """
    TODO : Renseigner la doc.
    """

    def __init__(self):
        if ClaspyTrainer is not None:
            self.core_version = cLASpy_Core_version
            self.claspy_classes = cLASpy_Classes
            self.trainer = ClaspyTrainer
        if algorithms is not None:
            self.algorithms = algorithms
        if cLASpy_T is not None:
            self.claspy_t_version = cLASpy_T.cLASpy_T_version
            self.claspy_t = cLASpy_T

        self.config: Settings = get_settings()

    def get_core_version(self) -> str:
        """
        Retourne la version du core du plugin cLASpy_ML.
        """
        if self.core_version is not None:
            return f"core_version : {self.core_version}"
        return "Plugin cLASpy_ML non chargé."

    def get_all_algorithms(self) -> List[str]:
        """
        Retourne la liste des algorithmes disponibles dans sklearn.ensemble.
        """
        if self.algorithms is None or algorithms is None:
            raise ModuleNotFoundError("Plugin cLASpy_ML non chargé.")

        algo_names = [
            name for name, obj in inspect.getmembers(self.algorithms, inspect.isclass)
            if not name.startswith("_")
        ]
        return algo_names

    def get_algorithm_parameters(self, name: str) -> Optional[Dict[str, dict]]:
        """
        Retourne les paramètres enrichis d'un algorithme sklearn.ensemble
        spécifié par son nom.
        """
        if self.algorithms is None or algorithms is None or enrich_algorithm_params is None:
            return None

        # Récupère la classe sklearn correspondante au nom
        algo_class = getattr(self.algorithms, name, None)
        if algo_class is None:
            raise ValueError(f"Algorithm '{name}' not found in sklearn.ensemble")

        # Instancie l'algorithme
        self.trainer = algo_class()

        # Retourne les paramètres enrichis
        return enrich_algorithm_params(self.trainer)

    async def load_data_file(self, file: UploadFile | None = None, fileInfos: dict | None = None,) -> str:
        """
        Charge un fichier .las ou .csv et retourne les infos du nuage de points.
        """
        if self.trainer is None:
            raise RuntimeError("cLASpy_Trainer non chargé")

        ALLOWED_EXTENSIONS = {'.las', '.csv'}

        # Détermine le path et l'extension
        if fileInfos:
            path = Path(fileInfos["full_path"])
            if not path.exists():
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=f"Fichier introuvable : {fileInfos['name']}"
                )
            suf = os.path.splitext(fileInfos['name'])[1].lower()
        elif file:
            path = None
            suf = os.path.splitext(file.filename)[1].lower()
        else:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Aucun fichier fourni"
            )

        # Valide l'extension
        if suf not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Type de fichier non supporté : {suf}"
            )

        # Cas 1 : fichier déjà sur le serveur
        if fileInfos:

            trainArgs = TrainArguments(
                input_data=str(path),
                output=str(path.parent),
                algo="rf",
            )

            # claspy_trainer = self.trainer(str(path))
            # claspy_trainer.data_type = suf
            # claspy_trainer.folder_path = str(path.parent)
            # claspy_trainer.config = None
            # claspy_trainer.input_data = str(path)
            # claspy_trainer.output = str(path.parent)

            self.claspy_t.train(trainArgs)
            return "train done"

        # Cas 2 : UploadFile temporaire
        assert file is not None
        content = await file.read()

        with tempfile.NamedTemporaryFile(delete=False, suffix=suf) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            claspy_trainer = self.trainer(tmp_path)
            claspy_trainer.folder_path = self.config.DEFAULT_OUTPUT_DIR
            return claspy_trainer.introduction()
        finally:
            os.remove(tmp_path)
