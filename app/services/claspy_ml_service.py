from datetime import datetime
import inspect
import os
from pathlib import Path
import tempfile
from typing import List, Optional, Dict
from fastapi import HTTPException, Request, UploadFile
from app.core.config import Settings, get_settings
from app.services.files_service import FileService

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

    def __init__(self, file_service: FileService):
        if ClaspyTrainer is not None:
            self.core_version = cLASpy_Core_version
            self.claspy_classes = cLASpy_Classes
            self.trainer = ClaspyTrainer
        if algorithms is not None:
            self.algorithms = algorithms
        if cLASpy_T is not None:
            self.claspy_t_version = cLASpy_T.cLASpy_T_version
            self.claspy_t = cLASpy_T

        self.file_service = file_service
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

    async def process_file(self, req: Request, keepOnServer: bool, folder_id: str,
                           file: UploadFile | None = None) -> dict:
        """
        Charge un fichier .las ou .csv et retourne les infos du nuage de points.
        """

        user_id = int(req.state.user.id)
        role_id = int(req.state.user.role_id)
        physical_path = None

        if keepOnServer:
            parent_id: str | None = None if folder_id.lower() == "root" else folder_id
            db_file = await self.file_service.save_file(file, user_id, role_id, parent_id)

            physical_path = await self.file_service.compute_physical_path(
                await self.file_service.get_file_by_id(db_file.id)
            )

            if not physical_path.exists():
                raise HTTPException(
                    status_code=500,
                    detail="Le fichier n'a pas été correctement sauvegardé sur le serveur"
                )

        if physical_path:
            return self.process_existing_file(physical_path)

        assert file is not None, "Aucun fichier fourni"
        return await self.process_temp_file(file)

    def process_existing_file(self, physical_path: Path) -> dict:
        """
        Traitement d'un fichier déjà présent sur le serveur.
        """
        path = Path(physical_path)
        return self.get_point_cloud_info(str(path), str(path.parent))

    async def process_temp_file(self, file: UploadFile) -> dict:
        """
        Sauvegarde et traite un fichier temporairement.
        """
        content = await file.read()
        temp_folder = self.config.TEMP_DIR
        os.makedirs(temp_folder, exist_ok=True)
        suffix = f"_{file.filename}"
        with tempfile.NamedTemporaryFile(
            delete=False, prefix="tmp_", suffix=suffix, dir=temp_folder
        ) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            now = datetime.now()
            timestamp_str = now.strftime("%Y%m%d_%H%M%S")
            output_path = Path(self.config.DEFAULT_OUTPUT_DIR) / timestamp_str
            os.makedirs(output_path, exist_ok=True)
            return self.get_point_cloud_info(str(tmp_path), str(output_path))
        finally:
            os.remove(tmp_path)

    def get_point_cloud_info(self, input_path: str, output_path: str) -> dict:
        if self.trainer is None:
            raise ModuleNotFoundError("Module ClaspyTrainer non chargé.")

        self.trainer = ClaspyTrainer(input_data=input_path, output_data=output_path)

        path_to_file = Path(input_path)
        filename = path_to_file.name

        return {
            "claspy_msg": self.trainer.point_cloud_info(),
            "details": f"Chargement du fichier : {filename} effectué avec succès.",
            "path": f"{Path(*path_to_file.parts[-4:]).as_posix()}"
        }
