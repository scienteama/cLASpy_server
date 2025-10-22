import subprocess
from pathlib import Path
from typing import Dict, List
from app.core.config import Settings
import sys
import pkg_resources
import json

config = Settings()

class ModulesService:
    """Service pour la gestion des modules cLASpy."""

    PLUGINS_FILE = config.PROJECT_ROOT / "plugins.json"

    @staticmethod
    def load_plugin(plugin_name: str) -> str:
        """Charge ou installe un plugin cLASpy à partir de son nom."""
        try:
            __import__(plugin_name)
            return plugin_name
        except ImportError:
            pass

        plugins_metadata = ModulesService._read_plugins_json()
        plugin_data = next((p for p in plugins_metadata if p["name"].lower() == plugin_name.lower()), None)

        if not plugin_data:
            raise ValueError(f"Plugin '{plugin_name}' non trouvé dans {ModulesService.PLUGINS_FILE}")

        link = plugin_data.get("link")
        if not link:
            raise ValueError(f"Plugin '{plugin_name}' n'a pas de lien d'installation défini")

        # pip install
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", link])
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Échec de l'installation du plugin '{plugin_name}': {e}")

        return plugin_name

    @staticmethod
    def unload_plugin(plugin_name: str) -> None:
        """Désinstalle un plugin cLASpy à partir de son nom."""
        subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", plugin_name])

    @staticmethod
    def list_claspy_modules() -> List[Dict[str, str]]:
        """
        Liste tous les modules cLASpy et leur état
        """
        plugins_metadata = ModulesService._read_plugins_json()

        # Rafraîchir le working_set pour détecter les installations récentes
        pkg_resources.working_set = pkg_resources.WorkingSet()
        installed_plugins = {dist.project_name.lower(): dist.version for dist in pkg_resources.working_set}

        plugins = []
        for plugin in plugins_metadata:
            normalized_name = plugin["name"].replace("_", "-").lower()
            plugins.append({
                "name": plugin["name"],
                "version": installed_plugins.get(normalized_name),
                "enable": normalized_name in installed_plugins,
                "description": plugin.get("description"),
                "tooltip": plugin.get("tooltip")
            })

        return plugins

    @staticmethod
    def _read_plugins_json() -> List[Dict[str, str]]:
        if not ModulesService.PLUGINS_FILE.exists():
            raise FileNotFoundError(f"Impossible de trouver {ModulesService.PLUGINS_FILE}")

        with open(ModulesService.PLUGINS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
