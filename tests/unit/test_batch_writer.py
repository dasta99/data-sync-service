"""Tests for TransactionalBatchWriter."""

import pytest
from unittest.mock import MagicMock
from load.upsert.loader import TransactionalBatchWriter
from tests.conftest import MockDatabase


@pytest.fixture
def writer():
    return TransactionalBatchWriter()


@pytest.fixture
def mock_dest():
    return MockDatabase()


class TestWrite:
    def test_commits_on_success(self, writer, mock_dest):
        rows = [{"id": "1", "name": "test"}]
        writer.write(mock_dest, "t", ["id", "name"], rows, 100, "INSERT INTO t VALUES (%s, %s)")
        assert mock_dest.committed

    def test_rollback_on_error(self, writer, mock_dest):
        mock_dest.cursor().executemany = MagicMock(side_effect=Exception("fail"))
        rows = [{"id": "1", "name": "test"}]

        with pytest.raises(Exception, match="fail"):
            writer.write(mock_dest, "t", ["id", "name"], rows, 100, "INSERT INTO t VALUES (%s, %s)")

        assert mock_dest.rolled_back

    def test_multiple_batches(self, writer, mock_dest):
        rows = [{"id": str(i), "name": f"row{i}"} for i in range(250)]
        writer.write(mock_dest, "t", ["id", "name"], rows, 100, "INSERT INTO t VALUES (%s, %s)")
        assert mock_dest.committed

    def test_empty_rows(self, writer, mock_dest):
        writer.write(mock_dest, "t", ["id"], [], 100, "INSERT INTO t VALUES (%s)")
        assert mock_dest.committed
