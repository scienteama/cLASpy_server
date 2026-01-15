from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from http import HTTPStatus
import inspect
import io
import os
from pathlib import Path
import tempfile
from typing import Any, List, Optional, Dict
import uuid
from fastapi import HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

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
    

    async def process_file(self, file: UploadFile | None = None, fileInfos: dict | None = None,) -> dict:
        """
        Charge un fichier .las ou .csv et retourne les infos du nuage de points.
        """

        # Cas 1 : fichier déjà sur le serveur
        if fileInfos:
            path = Path(fileInfos["full_path"])
            trainArgs = TrainArguments(
                input_data=str(Path(fileInfos["full_path"])),
                output=str(path.parent),
                algo="rf",
            )
            result = await run_in_threadpool(self._train_capture_sync, trainArgs)
            return result["stdout"]

        # Cas 2 : fichier temporaire
        assert file is not None
        content = await file.read()

        if file.filename:
            ext = os.path.splitext(file.filename)[1].lower()

        tempFolder = self.config.TEMP_DIR
        os.makedirs(tempFolder, exist_ok=True)
        suffix=f"_{file.filename}"

        with tempfile.NamedTemporaryFile(delete=False, prefix="tmp_", suffix=suffix or None, dir=tempFolder) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:

            now = datetime.now()
            timestamp_str = now.strftime("%Y%m%d_%H%M%S")
            output_path = Path(self.config.DEFAULT_OUTPUT_DIR) / timestamp_str
            
            trainArgs = TrainArguments(
                input_data=str(tmp_path),
                output=str(output_path),
                algo="rf",
            )

            self.trainer = ClaspyTrainer(trainArgs.input_data, output_data=trainArgs.output, algo=trainArgs.algo)

            path_to_file = Path(tmp_path)
            result = {
                "claspy_msg": self.trainer.point_cloud_info(),
                "details": f" Chargement du fichier : {file.filename} effectué avec succès.",
                "path": f"{Path(*path_to_file.parts[-4:]).as_posix()}"
            }

            return result
            # result = await run_in_threadpool(self._run_capture_sync, "train", trainArgs)
            #return result["stdout"]
        finally:
            print('temp_path :', tmp_path)
            #os.remove(tmp_path)

    async def load_data_file_stream(self, file, fileInfos):
        """
        Retourne un async generator ligne par ligne pour streamer stdout.
        """
        # Récupère le résultat complet de façon asynchrone dans un threadpool si besoin
        stdout = await self.load_data_file(file, fileInfos)  # load_data_file est async

        # Generator async pour renvoyer ligne par ligne
        for line in stdout.splitlines():
            yield line
