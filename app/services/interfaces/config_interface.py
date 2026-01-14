from app.core.config import Settings

class IConfigService:

    async def get_api_settings(self) -> dict:
        """
        Retourne les paramètres publiques de l'API.
        """
        ...