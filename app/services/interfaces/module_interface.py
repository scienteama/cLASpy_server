from typing import Dict, List, Protocol
from app.schemas.module_schema import ClaspyModule


class IModuleService(Protocol):
    def load_plugin(self, plugin_name: str) -> str:
        ...

    def unload_plugin(self, plugin_name: str) -> str:
        ...

    def list_claspy_modules(self) -> List[ClaspyModule]:
        ...

    def _read_plugins_json(self) -> List[Dict[str, str]]:
        ...

    def invalidate_cache(self):
        ...
