# ─── Sync Engine (backward compat) ──────────────────────────
from extract.query_builder import KeysetQueryBuilder
from load.upsert.loader import TransactionalBatchWriter
from extract.retry import SimpleRetryPolicy
from extract.worker import BaseSyncWorker
from extract.loop import run_sync_loop, cancel_table, get_running_tables, get_cancelled_tables

__all__ = [
    "KeysetQueryBuilder", "TransactionalBatchWriter",
    "SimpleRetryPolicy", "BaseSyncWorker", "run_sync_loop",
    "cancel_table", "get_running_tables", "get_cancelled_tables",
]
