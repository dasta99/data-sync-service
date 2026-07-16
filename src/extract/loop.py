"""Sync loops — orchestrates per-table and main sync cycles."""

import asyncio
import logging
from typing import Dict, Optional, Set

from shared.interfaces import Database
from shared.repositories import TableConfigRepository, WatermarkRepository
from shared.config import ConfigLoader
from shared.connections import PooledDatabaseFactory
from shared.mode import get_mode
from extract.worker import BaseSyncWorker
from extract.query_builder import KeysetQueryBuilder
from load.upsert.loader import TransactionalBatchWriter
from extract.retry import SimpleRetryPolicy
from extract.status import StatusWriter
from extract.history import HistoryLogger

logger = logging.getLogger("sync.loop")

_running_tasks: Dict[str, asyncio.Task] = {}
_cancelled_tables: Set[str] = set()

_loader = ConfigLoader()
_factory = PooledDatabaseFactory()


def cancel_table(table_name: str) -> bool:
    """Cancel a running sync for the given table. Returns True if cancelled."""
    if table_name in _running_tasks:
        _cancelled_tables.add(table_name)
        logger.info(f"[{table_name}] cancel requested")
        return True
    return False


def get_cancelled_tables() -> Set[str]:
    return set(_cancelled_tables)


def get_running_tables() -> list:
    return list(_running_tasks.keys())


def _get_source_db(name: str) -> Database:
    config = _loader.get_source(name)
    return _factory.get_or_create(f"source_{name}", config, pool_size=3)


def _build_worker(
    table_config: dict,
    dest_db: Database,
    on_sync_complete=None,
) -> BaseSyncWorker:
    return BaseSyncWorker(
        table_config=table_config,
        source=_get_source_db(table_config["source_name"]),
        dest=dest_db,
        query_builder=KeysetQueryBuilder(),
        batch_writer=TransactionalBatchWriter(),
        status=StatusWriter(dest_db),
        retry_policy=SimpleRetryPolicy(max_retries=3, delay=1.0),
        history_logger=HistoryLogger(dest_db),
        on_sync_complete=on_sync_complete,
    )


def _compute_sleep_interval(
    base_interval: int,
    consecutive_no_data: int,
    threshold: int,
    multiplier: int,
    max_interval: int,
) -> int:
    """Compute adaptive poll interval based on consecutive empty polls."""
    if consecutive_no_data < threshold:
        return base_interval
    exponent = consecutive_no_data - threshold
    interval = base_interval * (multiplier ** exponent)
    return min(interval, max_interval)


async def sync_table(
    table_config: dict,
    dest_db: Database,
    shutdown_event: asyncio.Event,
    on_sync_complete=None,
):
    """Sync a single table in a loop with adaptive polling."""
    table_name = table_config["table_name"]
    base_interval = table_config.get("poll_interval", 30)
    threshold = table_config.get("no_data_threshold", 2)
    multiplier = table_config.get("backoff_multiplier", 2)
    max_interval = table_config.get("max_poll_interval", 600)

    config_repo = TableConfigRepository(dest_db)
    watermark_repo = WatermarkRepository(dest_db)
    consecutive_no_data = 0

    while not shutdown_event.is_set():
        if table_name in _cancelled_tables:
            logger.info(f"[{table_name}] cancelled, stopping sync loop")
            _cancelled_tables.discard(table_name)
            status = StatusWriter(dest_db)
            status.mark_idle(table_name)
            break

        try:
            current_config = config_repo.get_table_config(table_name)
            if not current_config or not current_config["enabled"]:
                await asyncio.sleep(base_interval)
                continue

            watermark = watermark_repo.get_watermark(table_name)
            worker = _build_worker(current_config, dest_db, on_sync_complete)
            rows = worker.sync(watermark, watermark_repo=watermark_repo)

            if rows > 0:
                if consecutive_no_data > 0:
                    logger.info(f"[{table_name}] data resumed after {consecutive_no_data} empty polls, resetting interval to {base_interval}s")
                consecutive_no_data = 0
            else:
                consecutive_no_data += 1

        except Exception as e:
            logger.error(f"Error syncing {table_name}: {e}")

        sleep_sec = _compute_sleep_interval(base_interval, consecutive_no_data, threshold, multiplier, max_interval)

        if consecutive_no_data >= threshold:
            logger.debug(f"[{table_name}] no data, backing off to {sleep_sec}s (consecutive={consecutive_no_data})")

        for _ in range(sleep_sec):
            if shutdown_event.is_set() or table_name in _cancelled_tables:
                break
            await asyncio.sleep(1)


async def run_sync_loop(dest_db: Database, shutdown_event: asyncio.Event, on_sync_complete=None):
    """Main sync loop — spawns a coroutine per enabled table."""
    config_repo = TableConfigRepository(dest_db)

    logger.info("Sync service started")

    while not shutdown_event.is_set():
        try:
            tables = config_repo.get_enabled_tables()
            table_names = {t["table_name"] for t in tables}

            # Remove tasks for tables no longer enabled or cancelled
            for name in list(_running_tasks):
                if name not in table_names or name in _cancelled_tables:
                    task = _running_tasks.pop(name)
                    if not task.done():
                        task.cancel()

            # Spawn tasks for new enabled tables
            for t in tables:
                name = t["table_name"]
                if name not in _running_tasks or _running_tasks[name].done():
                    _running_tasks[name] = asyncio.create_task(
                        sync_table(t, dest_db, shutdown_event, on_sync_complete),
                        name=f"sync_{name}",
                    )

        except Exception as e:
            logger.error(f"Sync loop error: {e}")

        await asyncio.sleep(5)

    # Cancel all running tasks on shutdown
    for task in _running_tasks.values():
        if not task.done():
            task.cancel()
    _running_tasks.clear()

    logger.info("Sync service stopped")
