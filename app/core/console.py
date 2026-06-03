import sys
import io
import asyncio


class SocketConsole(io.TextIOBase):

    def __init__(self, ws_service, loop):
        self.ws_service = ws_service
        self.loop = loop

    def write(self, text):

        sys.__stdout__.write(text)

        if text:

            cleaned = text.replace("\r", "")

            self.loop.call_soon_threadsafe(
                lambda: asyncio.create_task(
                    self.ws_service.send_all("ml_task_progress", {"message": cleaned})
                )
            )

        if not text.strip() and text != "\n":
            return len(text)

    def flush(self):
        sys.__stdout__.flush()
