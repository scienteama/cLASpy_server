import sys
import io
import re
import asyncio

# Détecte les lignes de progression tqdm
# Ex: "Features at 1.0m:  44%|####4     | 400000/900000 [00:06<00:07, 64454.85points/s]"
_TQDM_RE = re.compile(
    r"^(?P<label>.+?):\s*(?P<percent>\d+)%\|[^|]*\|\s*"
    r"(?P<current>[\d]+)/(?P<total>[\d]+)\s+"
    r"\[(?P<elapsed>[^<]+)<(?P<eta>[^,\]]+)(?:,\s*(?P<speed>[^\]]+))?\]$"
)


class SocketConsole(io.TextIOBase):

    def __init__(self, ws_service, loop):
        self.ws_service = ws_service
        self.loop = loop

    def write(self, text):
        sys.__stdout__.write(text)

        cleaned = text.replace("\r", "").strip()
        if not cleaned:
            return len(text)

        m = _TQDM_RE.match(cleaned)
        if m:
            d = m.groupdict()
            payload = {
                "label": d["label"],
                "percent": int(d["percent"]),
                "current": int(d["current"]),
                "total": int(d["total"]),
                "elapsed": d["elapsed"].strip(),
                "eta": d["eta"].strip(),
                "speed": (d["speed"] or "").strip(),
            }
            self.loop.call_soon_threadsafe(
                lambda p=payload: asyncio.create_task(
                    self.ws_service.send_all("ml_task_feature_progress", p)
                )
            )
        else:
            self.loop.call_soon_threadsafe(
                lambda msg=cleaned: asyncio.create_task(
                    self.ws_service.send_all("ml_task_progress", {"message": msg})
                )
            )

        return len(text)

    def flush(self):
        sys.__stdout__.flush()
