import subprocess
from pathlib import Path
from app.core.config import Settings
import sys
import pkg_resources

config = Settings()

class ModulesService:
    """Service métier pour la gestion des modules cLASpy."""

    @staticmethod
    def load_plugin(plugin_name: str) -> str:
        """Charge ou installe un plugin cLASpy à partir de son nom."""
        try:
            __import__(plugin_name)
            return plugin_name
        except ImportError:
            pass
        req_path = config.PROJECT_ROOT/"plugins.txt"
        if not req_path.exists():
            raise FileNotFoundError(f"Impossible de trouver {req_path}")
        plugin_req_line = None
        with open(req_path, "r") as f:
            for line in f:
                line = line.strip()
                if "#egg=" in line and line.split("#egg=")[1] == plugin_name:
                    plugin_req_line = line
                    break
        if not plugin_req_line:
            raise ValueError(f"Plugin '{plugin_name}' non trouvé dans {req_path}")
        
        # pip install
        subprocess.check_call([sys.executable, "-m", "pip", "install", plugin_req_line])
        return plugin_name
    
    @staticmethod
    def unload_plugin(plugin_name: str) -> None:
        """Désinstalle un plugin cLASpy à partir de son nom."""
        subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", plugin_name])
        
    @staticmethod
    def list_installed_claspy_modules():
        """Liste les modules cLASpy installés dans l'environnement."""
        pkg_list = []
        for dist in pkg_resources.working_set:
            if dist.project_name.startswith("claspy-"):
                pkg_info = {
                    "name": dist.project_name,
                    "version": dist.version,
                }
                pkg_list.append(pkg_info)
        return pkg_list
    