from http import HTTPStatus
from celery import Celery
from fastapi import HTTPException
import httpx
import subprocess
import sys
import json
from typing import Dict, List
from functools import lru_cache
from importlib.metadata import distributions
from app.core.config import get_settings
from app.schemas.module_schema import ClaspyModule


class ModulesService:
    """Service pour la gestion des modules cLASpy."""

    config = get_settings()
    WORKER_MODULES = config.PROJECT_ROOT / "worker" / "modules"
    PLUGINS_FILE = config.PROJECT_ROOT / "plugins.json"
    DOCKER_COMPOSE_WORKER = config.PROJECT_ROOT / "docker-compose.worker.yml"

    @classmethod
    def load_plugin(cls, plugin_name: str) -> str:
        """
        Charge ou installe un plugin cLASpy à partir de son nom.
        """
        try:
            __import__(plugin_name)
            return plugin_name
        except ImportError:
            pass

        plugins_metadata = cls._read_plugins_json()
        plugin_data = next((p for p in plugins_metadata if p["name"].lower() == plugin_name.lower()), None)

        if not plugin_data:
            raise ValueError(f"Plugin '{plugin_name}' non trouvé dans {cls.PLUGINS_FILE}")

        link = plugin_data.get("link")
        egg = plugin_data.get("egg")
        if not link or not egg:
            raise ValueError(f"Plugin '{plugin_name}' est mal défini.")

        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", link])
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Échec lors de l'installation du plugin '{plugin_name}': {e}")

        # Invalidation du cache après installation
        cls.invalidate_cache()

        return f"Plugin '{plugin_name}' chargé avec succès"

    @classmethod
    def unload_plugin(cls, plugin_name: str) -> str:
        """Désinstalle un plugin cLASpy à partir de son nom."""
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", plugin_name])
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Échec de la désinstallation du plugin '{plugin_name}': {e}")

        # Invalidation du cache après suppression
        cls.invalidate_cache()

        return f"Plugin '{plugin_name}' déchargé aves succès"

    @classmethod
    @lru_cache(maxsize=1)
    def list_claspy_modules(cls) -> List["ClaspyModule"]:
        """Liste tous les modules cLASpy et leur état"""
        plugins_metadata = cls._read_plugins_json()

        # Liste des packages installés
        installed_plugins = {
            dist.metadata['Name'].lower(): dist.version
            for dist in distributions()
        }

        return [
            ClaspyModule(
                name=plugin["name"],
                version=installed_plugins.get(plugin["name"].lower()),
                enable=plugin["name"].lower() in installed_plugins,
                description=plugin.get("description"),
                tooltip=plugin.get("tooltip"),
            )
            for plugin in plugins_metadata
        ]

    @classmethod
    def _read_plugins_json(cls) -> List[Dict[str, str]]:
        """Lit le fichier JSON contenant les métadonnées des plugins."""
        if not cls.PLUGINS_FILE.exists():
            raise FileNotFoundError(f"Impossible de trouver {cls.PLUGINS_FILE}")

        with open(cls.PLUGINS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def invalidate_cache(cls):
        """Purge le cache des modules"""
        cls.list_claspy_modules.cache_clear()

    @classmethod
    async def list_workers(cls):
        """
        Interroge l'API Flower pour récupérer la liste des workers et leurs stats.
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                FLOWER_URL = "http://localhost:5556/api/workers"
                response = await client.get(FLOWER_URL, auth=(cls.config.FLOWER_USER, cls.config.FLOWER_PWD))
                response.raise_for_status()
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                    detail=f"Flower API unreachable: {str(e)}")
            except httpx.HTTPStatusError as e:
                raise HTTPException(status_code=response.status_code, detail=f"Flower API error: {response.text}")

        return response.json()

    @classmethod
    async def init_client_worker(cls, forceDisabled=False):
        modules = cls.list_claspy_modules()

        if forceDisabled:
            return None

        if any(mod.name == "taskrunner" and mod.enable for mod in modules):

            workers = await cls.list_workers()

            broker_url = f"amqp://{cls.config.RABBITMQ_DEFAULT_USER}:{cls.config.RABBITMQ_DEFAULT_PASS}@localhost:5672//"
            result_backend = f"redis://:{cls.config.REDIS_PASSWORD}@localhost:6379/0"

            worker = Celery(
                "taskrunner",
                broker=broker_url,
                backend=result_backend,
            )
            worker.conf.update(imports=["taskrunner.tasks.ml"])
            return worker
        else:
            return None
