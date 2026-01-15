from http import HTTPStatus
from fastapi import HTTPException
from app.core.config import get_settings


class ConfigService:
    """
    Service de gestion de la configuration.
    """

    def __init__(self):
        self.config = get_settings()

    async def get_api_settings(self):
        if not self.config:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Configuration non chargée."
            )
        return self.config.get_public_settings()
