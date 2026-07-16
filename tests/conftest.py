"""Shared test fixtures — mock Database, configs, watermarks."""

import pytest
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock

from shared.interfaces import Database, Cursor


class MockCursor(Cursor):
    """In-memory cursor for unit tests."""

    def __init__(self):
        self._results = []
        self._calls = []
        self._executemany_calls = []

    def execute(self, sql: str, params=None):
        self._calls.append((sql, params))
        return self

    def executemany(self, sql, params_list):
        self._executemany_calls.append((sql, params_list))

    def fetchall(self):
        return self._results

    def fetchone(self):
        return self._results[0] if self._results else None

    def close(self):
        pass

    def set_results(self, results):
        self._results = results


class MockDatabase(Database):
    """In-memory database for unit tests.

    Returns the SAME cursor instance on every cursor() call,
    so tests can pre-set results before the code under test runs.
    """

    def __init__(self):
        self._cursor = MockCursor()
        self.committed = False
        self.rolled_back = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        pass

    @property
    def last_sql(self):
        return self._cursor._calls[-1][0] if self._cursor._calls else None

    @property
    def last_params(self):
        return self._cursor._calls[-1][1] if self._cursor._calls else None


@pytest.fixture
def mock_db():
    return MockDatabase()


@pytest.fixture
def booth_voter_config():
    return {
        "table_name": "booth_voter",
        "source_name": "mytdp_remote",
        "source_table": "booth_voter",
        "dest_table": "booth_voter",
        "enabled": True,
        "poll_interval": 30,
        "batch_size": 500,
        "watermark_column": "updated_at",
        "primary_key": "id",
        "columns": ["id", "booth_id", "voter_id", "sir_verified", "updated_at"],
        "filters": ["sir_verified = 1"],
        "timezone_offset": 330,
    }


@pytest.fixture
def watermark():
    return {"last_timestamp": "2026-07-10 00:00:00", "last_id": "0"}
