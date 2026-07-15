"""Structured JSON logger for sync events."""

import json
import logging
import sys
from datetime import datetime, date

from shared.interfaces import SyncLogger

logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
_logger = logging.getLogger("sync")


class _SafeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return str(obj)


class SyncJsonLogger(SyncLogger):
    """Structured JSON logger — outputs one JSON line per event."""

    def __init__(self, table_name: str):
        self.table = table_name

    def _log(self, level: str, event: str, **kwargs):
        entry = {
            "event": event,
            "table": self.table,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs,
        }
        msg = json.dumps(entry, cls=_SafeEncoder)
        if level == "error":
            _logger.error(msg)
        else:
            _logger.info(msg)

    def sync_complete(self, rows: int, duration_ms: int):
        self._log("info", "sync_complete", rows=rows, duration_ms=duration_ms)

    def sync_error(self, error: str, attempt: int):
        self._log("error", "sync_error", error=str(error), retry=attempt)

    def no_data(self):
        self._log("info", "no_data")

    def watermark_update(self, ts, id):
        self._log("info", "watermark", last_ts=str(ts), last_id=str(id))
