"""Base sync worker — orchestrates one table's sync cycle."""

import time
from typing import Any, Dict, Optional

from sync.abstractions import (
    BatchWriter, Database, QueryBuilder, RetryPolicy,
    StatusTracker, SyncLogger,
)
from sync.monitoring.logger import SyncJsonLogger as ConcreteSyncLogger
from sync.monitoring.history import HistoryLogger


class BaseSyncWorker:
    """Syncs a single table using injected strategies."""

    def __init__(
        self,
        table_config: Dict[str, Any],
        source: Database,
        dest: Database,
        query_builder: QueryBuilder,
        batch_writer: BatchWriter,
        status: StatusTracker,
        retry_policy: RetryPolicy,
        log: Optional[SyncLogger] = None,
        history_logger: Optional[HistoryLogger] = None,
    ):
        self.config = table_config
        self.table_name = table_config["table_name"]
        self.source = source
        self.dest = dest
        self.query_builder = query_builder
        self.batch_writer = batch_writer
        self.status = status
        self.retry_policy = retry_policy
        self.log = log or ConcreteSyncLogger(self.table_name)
        self.history = history_logger

    def sync(self, watermark: Dict[str, Any], watermark_repo=None) -> int:
        """Execute one sync cycle. Returns rows synced."""
        self.status.mark_running(self.table_name)
        self.log._log("info", "sync_start", watermark=watermark)
        start_time = time.time()

        def _do_sync():
            rows = self._fetch_rows(watermark)
            duration_ms = int((time.time() - start_time) * 1000)

            if not rows:
                self.log.no_data()
                self.status.mark_success(self.table_name, 0, 0)
                if self.history:
                    self.history.log_success(self.table_name, 0, duration_ms)
                return 0

            self._write_rows(rows)

            new_ts = rows[-1][self.config["watermark_column"]]
            new_id = rows[-1][self.config["primary_key"]]

            if watermark_repo:
                watermark_repo.update_watermark(self.table_name, new_ts, new_id)

            self.log.sync_complete(len(rows), duration_ms)
            self.log.watermark_update(new_ts, new_id)
            self.status.mark_success(self.table_name, len(rows), duration_ms)

            if self.history:
                self.history.log_success(self.table_name, len(rows), duration_ms)

            return len(rows)

        try:
            return self.retry_policy.execute(_do_sync)
        except Exception as e:
            self.log.sync_error(str(e), 1)
            self.status.mark_error(self.table_name, str(e))
            if self.history:
                self.history.log_error(self.table_name, str(e))
            raise

    def _fetch_rows(self, watermark: Dict[str, Any]) -> list:
        query, params = self.query_builder.build_select(self.config, watermark)
        self.log._log("info", "fetch_start", query_preview=query[:200])
        cur = self.source.cursor()
        try:
            cur.execute(query, params)
            rows = cur.fetchall()
            self.log._log("info", "fetch_complete", row_count=len(rows))
            return rows
        finally:
            cur.close()

    def _write_rows(self, rows: list) -> None:
        upsert_sql = self.query_builder.build_upsert(self.config)
        self.log._log("info", "write_start", row_count=len(rows))
        self.batch_writer.write(
            dest=self.dest,
            table=self.config["dest_table"],
            columns=self.config["columns"],
            rows=rows,
            batch_size=self.config["batch_size"],
            upsert_sql=upsert_sql,
        )
        self.log._log("info", "write_complete")
