"""Tests for BaseSyncWorker."""

import pytest
from unittest.mock import MagicMock

from extract.worker import BaseSyncWorker
from extract.query_builder import KeysetQueryBuilder
from load.upsert.loader import TransactionalBatchWriter
from extract.retry import SimpleRetryPolicy
from extract.status import StatusWriter
from tests.conftest import MockDatabase


@pytest.fixture
def source_db():
    db = MockDatabase()
    db.cursor().set_results([
        {"id": "01HXYZ001", "booth_id": "B001", "voter_id": "V001",
         "sir_verified": 1, "updated_at": "2026-07-10 00:01:00"},
        {"id": "01HXYZ002", "booth_id": "B001", "voter_id": "V002",
         "sir_verified": 1, "updated_at": "2026-07-10 00:01:00"},
    ])
    return db


@pytest.fixture
def dest_db():
    return MockDatabase()


@pytest.fixture
def worker(source_db, dest_db, booth_voter_config):
    return BaseSyncWorker(
        table_config=booth_voter_config,
        source=source_db,
        dest=dest_db,
        query_builder=KeysetQueryBuilder(),
        batch_writer=TransactionalBatchWriter(),
        status=MagicMock(spec=StatusWriter),
        retry_policy=SimpleRetryPolicy(max_retries=1),
        log=MagicMock(),
    )


class TestSync:
    def test_returns_row_count(self, worker, watermark):
        assert worker.sync(watermark) == 2

    def test_calls_mark_running(self, worker, watermark):
        worker.sync(watermark)
        worker.status.mark_running.assert_called_once_with("booth_voter")

    def test_calls_mark_success(self, worker, watermark):
        worker.sync(watermark)
        worker.status.mark_success.assert_called_once()
        args = worker.status.mark_success.call_args
        assert args[0][0] == "booth_voter"
        assert args[0][1] == 2

    def test_logs_sync_complete(self, worker, watermark):
        worker.sync(watermark)
        worker.log.sync_complete.assert_called_once_with(2, pytest.approx(0, abs=10000))

    def test_logs_watermark(self, worker, watermark):
        worker.sync(watermark)
        worker.log.watermark_update.assert_called_once_with(
            "2026-07-10 00:01:00", "01HXYZ002"
        )

    def test_no_data_returns_zero(self, booth_voter_config):
        db = MockDatabase()
        db.cursor().set_results([])
        dest = MockDatabase()

        worker = BaseSyncWorker(
            table_config=booth_voter_config,
            source=db,
            dest=dest,
            query_builder=KeysetQueryBuilder(),
            batch_writer=TransactionalBatchWriter(),
            status=MagicMock(spec=StatusWriter),
            retry_policy=SimpleRetryPolicy(max_retries=1),
            log=MagicMock(),
        )

        result = worker.sync({"last_timestamp": "2026-07-10 00:00:00", "last_id": "0"})
        assert result == 0
        worker.log.no_data.assert_called_once()

    def test_updates_watermark_repo(self, source_db, dest_db, booth_voter_config, watermark):
        watermark_repo = MagicMock()
        worker = BaseSyncWorker(
            table_config=booth_voter_config,
            source=source_db,
            dest=dest_db,
            query_builder=KeysetQueryBuilder(),
            batch_writer=TransactionalBatchWriter(),
            status=MagicMock(spec=StatusWriter),
            retry_policy=SimpleRetryPolicy(max_retries=1),
        )
        worker.sync(watermark, watermark_repo=watermark_repo)
        watermark_repo.update_watermark.assert_called_once_with(
            "booth_voter", "2026-07-10 00:01:00", "01HXYZ002"
        )

    def test_error_calls_mark_error(self, source_db, dest_db, booth_voter_config, watermark):
        source_db.cursor().execute = MagicMock(side_effect=Exception("db fail"))
        status = MagicMock(spec=StatusWriter)
        log = MagicMock()

        worker = BaseSyncWorker(
            table_config=booth_voter_config,
            source=source_db,
            dest=dest_db,
            query_builder=KeysetQueryBuilder(),
            batch_writer=TransactionalBatchWriter(),
            status=status,
            retry_policy=SimpleRetryPolicy(max_retries=1),
            log=log,
        )

        with pytest.raises(Exception):
            worker.sync(watermark)

        status.mark_error.assert_called_once()
        log.sync_error.assert_called_once()
