from http import HTTPStatus
import inspect
from pathlib import Path
from typing import List, Optional, Dict
from fastapi import HTTPException, Request, UploadFile
import joblib
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from app.core.config import Settings, get_settings
from app.schemas.train_schema import ModelInfo, PointCloudInfo, PredictParameters, TrainParameters
from app.services.files_service import FileService
from app.services.worker_service import WorkerService
from app.utils.claspy_ml_utils import parse_cloud_points_info

try:
    from cLASpy_ML import cLASpy_Classes
    from cLASpy_ML import cLASpy_T
    from cLASpy_ML.cLASpy_Classes import ClaspyTrainer, cLASpy_Core_version
    import sklearn.ensemble as algorithms
    import sklearn.neural_network as nn
    from app.utils.claspy_ml_utils import enrich_algorithm_params
except ModuleNotFoundError:
    cLASpy_Classes = None
    cLASpy_T = None
    ClaspyTrainer = None
    cLASpy_Core_version = None
    algorithms = None
    nn = None
    enrich_algorithm_params = None
    pass


class ClaspyMLService:
    """
    TODO : Renseigner la doc.
    """

    def __init__(self, file_service: FileService, worker_service: WorkerService):
        if ClaspyTrainer is not None:
            self.core_version = cLASpy_Core_version
            self.claspy_classes = cLASpy_Classes
            self.trainer = ClaspyTrainer
        if algorithms is not None:
            self.algorithms = algorithms
        if nn is not None:
            self.neural_network = nn
        if cLASpy_T is not None:
            self.claspy_t_version = cLASpy_T.cLASpy_T_version
            self.claspy_t = cLASpy_T

        self.file_service = file_service
        self.worker_service = worker_service
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
        algos_names = [
            name
            for name, obj in inspect.getmembers(self.algorithms, inspect.isclass)
            if not name.startswith("_") and "Regressor" not in name
        ]

        neural_network_algos = [
            name
            for name, obj in inspect.getmembers(self.neural_network, inspect.isclass)
            if not name.startswith("_") and "Regressor" not in name
        ]

        return algos_names + neural_network_algos

    def get_algorithm_parameters(self, name: str) -> Optional[Dict[str, dict]]:
        """
        Retourne les paramètres enrichis d'un algorithme sklearn.ensemble
        spécifié par son nom.
        """
        try:

            if name in ["MLPClassifier", "MLPRegressor"]:
                sklearn_class = self.neural_network
            else:
                sklearn_class = self.algorithms

            # Récupère la classe sklearn correspondante au nom
            algo_class = getattr(sklearn_class, name, None)
            if algo_class is None:
                raise ValueError(f"Erreur '{name}' Non trouvé.")

            # Retourne les paramètres enrichis
            return enrich_algorithm_params(algo_class())

        except TypeError as t:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la récupération des paramètres pour '{name}' : {t}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors du traitement de l'algorithme '{name}' : {e}",
            )

    async def upload_file(
        self, req: Request, folder_id: str, file: UploadFile | None = None
    ) -> PointCloudInfo:
        """
        Upload un fichier .las ou .csv et retourne les infos du nuage de points.
        """
        user_id = int(req.state.user.id)
        role_id = int(req.state.user.role_id)
        physical_path = None

        parent_id: str | None = None if folder_id.lower() == "root" else folder_id
        db_file = await self.file_service.save_file(file, user_id, role_id, parent_id)

        physical_path = await self.file_service.compute_physical_path(
            await self.file_service.get_file_by_id(db_file.id)
        )

        if not physical_path.exists():
            raise HTTPException(
                status_code=500,
                detail="Le fichier n'a pas été correctement sauvegardé sur le serveur",
            )

        return self.process_existing_file(physical_path)

    async def load_file(self, file_id: str) -> PointCloudInfo:
        """
        Charge un fichier .las ou .csv déja existant et retourne les infos du nuage de points.
        """
        if file_id is None:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail="Id fichier invalide ou manquant"
            )

        file = await self.file_service.get_file_by_id(file_id)

        if file is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Fichier non trouvé")

        file_path = await self.file_service.compute_physical_path(file)

        return self.process_existing_file(file_path)

    def process_existing_file(self, physical_path: Path) -> PointCloudInfo:
        """
        Traitement d'un fichier déjà présent sur le serveur.
        """
        path = Path(physical_path)
        return self.get_point_cloud_info(str(path), str(path.parent))

    def get_point_cloud_info(self, input_path: str, output_path: str) -> PointCloudInfo:
        if self.trainer is None:
            raise RuntimeError("ClaspyTrainer n'a pas été initialisé")

        self.trainer = ClaspyTrainer(input_data=input_path, output_data=output_path)

        self.get_data_features()

        path_to_file = Path(input_path)
        filename = path_to_file.name

        # Charge les informations de base du fichier
        file_infos = parse_cloud_points_info(self.trainer.point_cloud_info(), filename)
        # Charge la liste des features
        file_infos.feat_list = self.get_data_features()

        return file_infos

    def get_data_features(self) -> List[str]:
        if self.trainer is None:
            raise RuntimeError("ClaspyTrainer n'a pas été initialisé")
        return self.trainer.get_data_features()

    async def run_prediction(self, req: Request, params: PredictParameters):
        """
        Lance une prédiction avec les paramètres spécifiés.
        """

        if not params.file_id or not params.model_id:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Id fichier ou Id modèle invalide ou manquant",
            )

        params.user_id = int(req.state.user.id)
        params.role_id = int(req.state.user.role_id)

        file = await self.file_service.get_file_by_id(params.file_id)
        file_path = await self.file_service.compute_physical_path(file)
        model_file = await self.file_service.get_file_by_id(params.model_id)
        model_path = await self.file_service.compute_physical_path(model_file)

        if params.folder_id != "root":
            folder = await self.file_service.get_file_by_id(params.folder_id)
            params.output = str(await self.file_service.compute_physical_path(folder))
        else:
            params.output = str(model_path.parent)

        params.input_data = str(file_path)
        params.model = str(model_path)

        result = self.claspy_t.predict(arguments=params)

        return await self.file_service.save_ml_result(
            result, params.user_id, params.role_id, params.folder_id, ml_type="prediction"
        )

    async def run_train(self, req: Request, params: TrainParameters):
        """
        Lance un entraînement avec les paramètres spécifiés.
        """
        if not params.file_id:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail="Id fichier invalide ou manquant"
            )

        params.user_id = int(req.state.user.id)
        params.role_id = int(req.state.user.role_id)

        file = await self.file_service.get_file_by_id(params.file_id)
        file_path = await self.file_service.compute_physical_path(file)

        if params.folder_id != "root":
            folder = await self.file_service.get_file_by_id(params.folder_id)
            params.output = str(await self.file_service.compute_physical_path(folder))
        else:
            params.output = str(file_path.parent)

        params.input_data = str(file_path)
        params.algo = self.claspy_t.shortname_algo(params.algorithm)

        if self.config.ENV == "desktop":
            params.no_worker = True

        state = await self.worker_service.get_worker_state(params.no_worker)
        if state.is_enabled and state.has_workers:
            task_id = state.celery.send_task(
                "taskrunner.tasks.ml.train_task",
                args=[params.model_dump(), "Entraînement démarré"],
                queue="ml",
            )

            return f"Tâche n'° {task_id} ajoutée avec succès."

        elif params.no_worker:
            result = self.claspy_t.train(arguments=params)
            return await self.file_service.save_ml_result(
                result, params.user_id, params.role_id, params.folder_id
            )
        else:
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="Aucun worker n'est actuellement actif.",
            )

    async def get_model_info(self, model_id: str) -> ModelInfo:
        """
        Charge un modèle de classification dans l'interface.
         - Vérifie l'extension du fichier
         - Récupère les informations du modèle (algorithme, scaler, PCA, paramètres)
         - Met à jour l'interface avec les informations du modèle
        """

        model_file = await self.file_service.get_file_by_id(model_id)
        model_path = await self.file_service.compute_physical_path(model_file)

        try:
            loaded_model = joblib.load(model_path)
        except Exception as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors du chargement du modèle : {str(e)}",
            )

        # Retrieve algorithm, model
        algorithm = loaded_model["algorithm"]
        model = loaded_model["model"]

        # Check if model created by GridSearchCV or Pipeline
        if isinstance(model, GridSearchCV):
            model = model.best_estimator_
        elif isinstance(model, Pipeline):
            pass
        else:
            raise ValueError("Model load failed! Model must be GridSearchCV or Pipeline!")

        # Scaler
        scaler = model["scaler"]

        # PCA
        try:
            if model["pca"]:
                pca = model["pca"].get_params()["n_components"]
                pca = str(pca) + " components"
            else:
                pca = "No PCA applied"
        except KeyError:
            pca = "No PCA applied"

        features = loaded_model["feature_names"]

        # Parameters
        algo_parameters = list[str]()
        dict_algo_param = model["classifier"].get_params()
        for key in dict_algo_param:
            algo_parameters.append(str(key) + ": " + str(dict_algo_param[key]) + "\n")

        return ModelInfo(
            model_name=model_file.logical_name,
            scaler=str(scaler),
            pca=pca,
            feat_list=features,
            algo_name=algorithm,
            parameters=algo_parameters,
        )
