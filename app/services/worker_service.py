import time
from app.core.config import get_settings
from app.models.celery import WorkerState
from app.services.modules_service import ModulesService
from kombu.exceptions import OperationalError

try:
    from taskrunner.main import make_celery
    from taskrunner.manager import WorkerManager
except ModuleNotFoundError as e:
    pass


class WorkerService:

    def __init__(self, m_service: ModulesService):
        self.m_service = m_service
        self.config = get_settings()

    async def get_worker_state(self, no_worker=False):

        if no_worker:
            return WorkerState(celery=None, workers={})

        modules = self.m_service.list_claspy_modules()

        taskrunner_enabled = any(
            mod.name == "taskrunner" and mod.enable
            for mod in modules
        )

        if not taskrunner_enabled:
            return WorkerState(celery=None, workers={})

        celery = make_celery(
            broker_url=f"amqp://{self.config.RABBITMQ_DEFAULT_USER}:{self.config.RABBITMQ_DEFAULT_PASS}@localhost:5672//",
            result_backend=f"redis://:{self.config.REDIS_PASSWORD}@localhost:6379/0"
        )

        workers = await self._safe_get_workers(celery)

        return WorkerState(
            celery=celery,
            workers=workers
        )

    async def _safe_get_workers(
        self,
        celery,
        retries: int = 1,
        timeout: float = 1.5,
        backoff: float = 0.5,
    ):
        """
        Récupère les workers avec retry + timeout.
        """

        for attempt in range(retries):
            try:
                # ping pour vérifier disponibilité
                celery.control.ping(timeout=timeout)

                # si ping OK on récupère le worker
                return WorkerManager.get_worker_pids(celery) or {}

            except OperationalError:

                if attempt == retries - 1:
                    return {}

            except Exception:
                if attempt == retries - 1:
                    return {}

            time.sleep(backoff * (attempt + 1))

        return {}
