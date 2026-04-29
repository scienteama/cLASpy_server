from typing import Optional, Dict

try:
    from taskrunner.main import Celery
except ModuleNotFoundError:
    Celery = None


class WorkerState:
    def __init__(self, celery: Optional["Celery"] = None, workers: Dict[str, int] = None):
        self.celery = celery
        self.workers = workers or {}

    @property
    def is_enabled(self) -> bool:
        return self.celery is not None

    @property
    def has_workers(self) -> bool:
        return bool(self.workers)
