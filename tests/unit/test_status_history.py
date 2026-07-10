"""Tests for StatusWriter and HistoryLogger."""

import pytest
from sync.monitoring.status import StatusWriter
from sync.monitoring.history import HistoryLogger
from tests.conftest import MockDatabase


@pytest.fixture
def db():
    return MockDatabase()


@pytest.fixture
def status_writer(db):
    return StatusWriter(db)


@pytest.fixture
def history_logger(db):
    return HistoryLogger(db)


class TestStatusWriter:
    def test_mark_running(self, status_writer, db):
        status_writer.mark_running("booth_voter")
        assert db.committed
        assert "INSERT INTO sync_status" in db.last_sql
        assert "running" in db.last_sql

    def test_mark_success(self, status_writer, db):
        status_writer.mark_success("booth_voter", rows=100, duration_ms=5000)
        assert db.committed
        assert "UPDATE sync_status" in db.last_sql
        assert "idle" in db.last_sql

    def test_mark_error(self, status_writer, db):
        status_writer.mark_error("booth_voter", "connection timeout")
        assert db.committed
        assert "error" in db.last_sql

    def test_get_all_status(self, status_writer, db):
        db.cursor().set_results([{"table_name": "booth_voter", "status": "idle"}])
        result = status_writer.get_all_status()
        assert len(result) == 1
        assert result[0]["table_name"] == "booth_voter"

    def test_get_table_status(self, status_writer, db):
        db.cursor().set_results([{"table_name": "booth_voter", "status": "idle"}])
        result = status_writer.get_table_status("booth_voter")
        assert result["table_name"] == "booth_voter"


class TestHistoryLogger:
    def test_log_success(self, history_logger, db):
        history_logger.log_success("booth_voter", rows=500, duration_ms=3000)
        assert db.committed
        # Last cursor call is the prune DELETE, INSERT was called before
        all_sql = [c._calls[0][0] for c in [db._cursor] if c._calls]
        assert any("INSERT INTO sync_history" in sql for sql in all_sql)

    def test_log_error(self, history_logger, db):
        history_logger.log_error("booth_voter", "timeout")
        assert db.committed
        assert "INSERT INTO sync_history" in db.last_sql

    def test_get_history(self, history_logger, db):
        db.cursor().set_results([
            {"status": "success", "rows_synced": 500, "duration_ms": 3000,
             "error_message": None, "started_at": "2026-07-10 00:00:00",
             "completed_at": "2026-07-10 00:00:03"}
        ])
        result = history_logger.get_history("booth_voter")
        assert len(result) == 1
        assert result[0]["status"] == "success"

    def test_prune_keeps_max_history(self, history_logger, db):
        history_logger.log_success("booth_voter", rows=100, duration_ms=1000)
        assert "DELETE FROM sync_history" in db.last_sql

    def test_get_history_with_limit(self, history_logger, db):
        history_logger.get_history("booth_voter", limit=5)
        assert "LIMIT %s" in db.last_sql
