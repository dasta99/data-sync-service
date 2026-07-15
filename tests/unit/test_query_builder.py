"""Tests for KeysetQueryBuilder."""

import pytest
from extract.query_builder import KeysetQueryBuilder


@pytest.fixture
def builder():
    return KeysetQueryBuilder()


class TestBuildSelect:
    def test_basic_query(self, builder, booth_voter_config, watermark):
        sql, params = builder.build_select(booth_voter_config, watermark)

        assert "SELECT" in sql
        assert "booth_voter" in sql
        assert "updated_at > %s" in sql
        assert "id > %s" in sql
        assert params == ("2026-07-10 00:00:00", "2026-07-10 00:00:00", "0")

    def test_query_has_order_by(self, builder, booth_voter_config, watermark):
        sql, _ = builder.build_select(booth_voter_config, watermark)
        assert "ORDER BY updated_at, id" in sql

    def test_query_has_limit(self, builder, booth_voter_config, watermark):
        sql, _ = builder.build_select(booth_voter_config, watermark)
        assert "LIMIT 500" in sql

    def test_filter_applied(self, builder, booth_voter_config, watermark):
        sql, _ = builder.build_select(booth_voter_config, watermark)
        assert "sir_verified = 1" in sql

    def test_no_filters(self, builder, watermark):
        config = {"columns": ["id"], "source_table": "t", "watermark_column": "updated_at",
                  "primary_key": "id", "batch_size": 100, "filters": []}
        sql, _ = builder.build_select(config, watermark)
        assert "WHERE" in sql
        assert "sir_verified" not in sql

    def test_watermark_with_timestamp(self, builder, booth_voter_config):
        wm = {"last_timestamp": "2026-07-10 12:30:00", "last_id": "99999"}
        _, params = builder.build_select(booth_voter_config, wm)
        assert params == ("2026-07-10 12:30:00", "2026-07-10 12:30:00", "99999")


class TestBuildUpsert:
    def test_upsert_with_update(self, builder, booth_voter_config):
        sql = builder.build_upsert(booth_voter_config)

        assert "INSERT INTO booth_voter" in sql
        assert "ON DUPLICATE KEY UPDATE" in sql
        assert "VALUES (%s, %s, %s, %s, %s)" in sql

    def test_upsert_excludes_pk_from_update(self, builder, booth_voter_config):
        sql = builder.build_upsert(booth_voter_config)
        # id is the PK, should not be in UPDATE clause
        update_section = sql.split("ON DUPLICATE KEY UPDATE")[1]
        assert "id = VALUES(id)" not in update_section

    def test_upsert_no_columns(self, builder):
        config = {"dest_table": "t", "primary_key": "id", "columns": ["id"]}
        sql = builder.build_upsert(config)
        assert "INSERT IGNORE" in sql
