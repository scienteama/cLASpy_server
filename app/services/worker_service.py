from app.core.config import get_settings
from app.models.celery import WorkerState
from app.services.modules_service import ModulesService

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

        workers = WorkerManager.get_worker_pids(celery) or {}

        return WorkerState(
            celery=celery,
            workers=workers
        )
