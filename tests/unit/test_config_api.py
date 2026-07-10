"""Tests for Config CRUD API routes."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


def _make_mock_repo():
    repo = MagicMock()
    repo.get_enabled_tables.return_value = [
        {
            "table_name": "booth_voter",
            "source_name": "mytdp_remote",
            "source_table": "booth_voter",
            "dest_table": "booth_voter",
            "enabled": True,
            "poll_interval": 30,
            "batch_size": 500,
            "watermark_column": "updated_at",
            "primary_key": "id",
            "columns": ["id", "booth_id"],
            "filters": ["sir_verified = 1"],
            "timezone_offset": 330,
            "no_data_threshold": 2,
            "backoff_multiplier": 2,
            "max_poll_interval": 600,
        }
    ]
    repo.get_all_tables.return_value = repo.get_enabled_tables.return_value
    repo.get_table_config.return_value = repo.get_enabled_tables.return_value[0]
    repo.create.return_value = {
        "table_name": "new_table",
        "source_name": "local",
        "source_table": "new_table",
        "dest_table": "new_table",
        "enabled": True,
        "poll_interval": 30,
        "batch_size": 500,
        "watermark_column": "updated_at",
        "primary_key": "id",
        "columns": [],
        "filters": [],
        "timezone_offset": 0,
        "no_data_threshold": 2,
        "backoff_multiplier": 2,
        "max_poll_interval": 600,
    }
    repo.update.return_value = {
        "table_name": "booth_voter",
        "source_name": "local",
        "source_table": "booth_voter",
        "dest_table": "booth_voter",
        "enabled": True,
        "poll_interval": 60,
        "batch_size": 500,
        "watermark_column": "updated_at",
        "primary_key": "id",
        "columns": ["id", "booth_id"],
        "filters": ["sir_verified = 1"],
        "timezone_offset": 330,
        "no_data_threshold": 2,
        "backoff_multiplier": 2,
        "max_poll_interval": 600,
    }
    repo.delete.return_value = True
    return repo


@pytest.fixture
def client():
    with patch("sync.api.config._get_repo") as mock:
        mock.return_value = _make_mock_repo()
        from sync.api.config import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router, prefix="/config")
        yield TestClient(app)


class TestListConfigs:
    def test_list_enabled_only(self, client):
        resp = client.get("/config")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["tables"][0]["table_name"] == "booth_voter"

    def test_list_all(self, client):
        resp = client.get("/config?enabled_only=false")
        assert resp.status_code == 200


class TestGetConfig:
    def test_get_existing(self, client):
        resp = client.get("/config/booth_voter")
        assert resp.status_code == 200
        assert resp.json()["table_name"] == "booth_voter"

    def test_get_not_found(self, client):
        with patch("sync.api.config._get_repo") as mock:
            repo = _make_mock_repo()
            repo.get_table_config.return_value = None
            mock.return_value = repo
            from sync.api.config import router
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router, prefix="/config")
            c = TestClient(app)
            resp = c.get("/config/nonexistent")
            assert resp.status_code == 404


class TestCreateConfig:
    def test_create_success(self, client):
        with patch("sync.api.config._get_repo") as mock:
            repo = _make_mock_repo()
            repo.get_table_config.return_value = None
            mock.return_value = repo
            from sync.api.config import router
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router, prefix="/config")
            c = TestClient(app)
            resp = c.post("/config", json={
                "table_name": "new_table",
                "source_name": "local",
                "source_table": "new_table",
                "dest_table": "new_table",
            })
            assert resp.status_code == 201
            assert resp.json()["table_name"] == "new_table"

    def test_create_conflict(self, client):
        with patch("sync.api.config._get_repo") as mock:
            repo = _make_mock_repo()
            repo.get_table_config.return_value = {"table_name": "booth_voter"}
            mock.return_value = repo
            from sync.api.config import router
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router, prefix="/config")
            c = TestClient(app)
            resp = c.post("/config", json={
                "table_name": "booth_voter",
                "source_name": "local",
                "source_table": "t",
                "dest_table": "t",
            })
            assert resp.status_code == 409

    def test_create_validation_error(self, client):
        resp = client.post("/config", json={"table_name": "x"})
        assert resp.status_code == 422


class TestUpdateConfig:
    def test_update_success(self, client):
        resp = client.put("/config/booth_voter", json={"poll_interval": 60})
        assert resp.status_code == 200
        assert resp.json()["poll_interval"] == 60

    def test_update_not_found(self, client):
        with patch("sync.api.config._get_repo") as mock:
            repo = _make_mock_repo()
            repo.get_table_config.return_value = None
            mock.return_value = repo
            from sync.api.config import router
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router, prefix="/config")
            c = TestClient(app)
            resp = c.put("/config/nonexistent", json={"poll_interval": 60})
            assert resp.status_code == 404

    def test_update_empty_body(self, client):
        resp = client.put("/config/booth_voter", json={})
        assert resp.status_code == 200


class TestDeleteConfig:
    def test_delete_success(self, client):
        resp = client.delete("/config/booth_voter")
        assert resp.status_code == 200
        assert resp.json()["deleted"] == "booth_voter"

    def test_delete_not_found(self, client):
        with patch("sync.api.config._get_repo") as mock:
            repo = _make_mock_repo()
            repo.delete.return_value = False
            mock.return_value = repo
            from sync.api.config import router
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router, prefix="/config")
            c = TestClient(app)
            resp = c.delete("/config/nonexistent")
            assert resp.status_code == 404
