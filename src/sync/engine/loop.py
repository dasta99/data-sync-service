"""Sync loops — orchestrates per-table and main sync cycles."""

import asyncio
import logging
from typing import Optional

from sync.abstractions import Database
from sync.container import get_source_db, get_config_repo, get_watermark_repo
from sync.engine.worker import BaseSyncWorker
from sync.engine.query_builder import KeysetQueryBuilder
from sync.engine.batch_writer import TransactionalBatchWriter
from sync.engine.retry import SimpleRetryPolicy
from sync.monitoring.status import StatusWriter
from sync.monitoring.history import HistoryLogger

logger = logging.getLogger("sync.loop")


def _build_worker(table_config: dict, dest_db: Database) -> BaseSyncWorker:
    return BaseSyncWorker(
        table_config=table_config,
        source=get_source_db(table_config["source_name"]),
        dest=dest_db,
        query_builder=KeysetQueryBuilder(),
        batch_writer=TransactionalBatchWriter(),
        status=StatusWriter(dest_db),
        retry_policy=SimpleRetryPolicy(max_retries=3, delay=1.0),
        history_logger=HistoryLogger(dest_db),
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


async def sync_table(table_config: dict, dest_db: Database, shutdown_event: asyncio.Event):
    """Sync a single table in a loop with adaptive polling."""
    table_name = table_config["table_name"]
    base_interval = table_config.get("poll_interval", 30)
    threshold = table_config.get("no_data_threshold", 2)
    multiplier = table_config.get("backoff_multiplier", 2)
    max_interval = table_config.get("max_poll_interval", 600)

    config_repo = get_config_repo(dest_db)
    watermark_repo = get_watermark_repo(dest_db)
    consecutive_no_data = 0

    while not shutdown_event.is_set():
        try:
            current_config = config_repo.get_table_config(table_name)
            if not current_config or not current_config["enabled"]:
                await asyncio.sleep(base_interval)
                continue

            watermark = watermark_repo.get_watermark(table_name)
            worker = _build_worker(current_config, dest_db)
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
            if shutdown_event.is_set():
                break
            await asyncio.sleep(1)


async def run_sync_loop(dest_db: Database, shutdown_event: asyncio.Event):
    """Main sync loop — spawns a coroutine per enabled table."""
    config_repo = get_config_repo(dest_db)

    logger.info("Sync service started")

    while not shutdown_event.is_set():
        try:
            tables = config_repo.get_enabled_tables()
            if not tables:
                logger.info("No enabled tables, waiting...")
                await asyncio.sleep(10)
                continue

            await asyncio.gather(*(sync_table(t, dest_db, shutdown_event) for t in tables))
        except Exception as e:
            logger.error(f"Sync loop error: {e}")
            await asyncio.sleep(5)

    logger.info("Sync service stopped")
