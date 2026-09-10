from contextlib import redirect_stderr
from fastapi import Request
from app.schemas.notification_schema import NotificationType
from app.services.notifications_service import NotificationService
from app.services.ws_service import SocketIOService
import asyncio
import threading
from concurrent.futures import Future
from contextlib import redirect_stdout
from app.core.console import SocketConsole
from app.schemas.train_schema import FeatureComputationParameters
from app.services.files_service import FileService

try:
    from claspy_features import ClaspyFeature
except ModuleNotFoundError:
    ClaspyFeature = None


class ClaspyFeatService:
    """
    cLASpy_T class to compute features of a point cloud according several search radius.
    """

    def __init__(
        self,
        file_service: FileService,
        ws_service: SocketIOService,
        notif_service: NotificationService,
    ):
        """
        Initialize cLASpyFeat object.
        """
        if ClaspyFeature is not None:
            self.claspy_feat = ClaspyFeature

        self.file_service = file_service
        self.ws_service = ws_service
        self.notif_service = notif_service

    async def compute_features(self, req: Request, params: FeatureComputationParameters):
        """
        Compute features of a point cloud according several search radius.
        """

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

        loop = asyncio.get_running_loop()
        console = SocketConsole(self.ws_service, loop)
        result_future = Future()

        def task():
            with redirect_stdout(console), redirect_stderr(console):
                self.claspy_feat = ClaspyFeature(
                    input_data=params.input_data,
                    output_data=params.output,
                    feature_names=params.feature_names,
                    search_radius=params.search_radius,
                    n_jobs=params.n_jobs,
                    batch_size=params.batch_size,
                )
                result = self.claspy_feat.compute_features()
                self.claspy_feat.save_point_cloud()
                result_future.set_result(result)

        thread = threading.Thread(target=task)
        thread.start()

        await self.notif_service.create_notification(
            params.user_id,
            message=f"Features calculées avec succès pour : {file.logical_name}.",
            notif_type=NotificationType.ML_FEATURES,
            sender_id=None,
        )

        return "Features computed"
