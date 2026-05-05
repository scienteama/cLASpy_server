import asyncio
from collections import deque
from datetime import datetime, timezone
import logging
import os
import psutil
from app.services.ws_service import SocketIOService

MAX_HISTORY = 180
cpu_history = deque(maxlen=MAX_HISTORY)
ram_history = deque(maxlen=MAX_HISTORY)
logger = logging.getLogger("app")


async def metrics_loop(ws_service: SocketIOService):
    last_cpu_save = 0.0
    last_ram_save = 0.0

    while True:
        if ws_service.active_users:

            now = datetime.now(timezone.utc)
            now_ts = now.timestamp()

            try:

                metrics = {
                    "cpu_percent": psutil.cpu_percent(interval=None),
                    "ram_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage(os.path.abspath(os.sep)).percent,
                    "timestamp": now.isoformat(),
                }
            except Exception as e:
                logger.error(e)

            # CPU history
            if now_ts - last_cpu_save >= 10:
                cpu_history.append({"t": now_ts, "v": metrics["cpu_percent"]})
                last_cpu_save = now_ts

            # RAM history
            if now_ts - last_ram_save >= 10:
                ram_history.append({"t": now_ts, "v": metrics["ram_percent"]})
                last_ram_save = now_ts

            # Stream
            await ws_service.send_all("metrics", metrics)

        await asyncio.sleep(1)
