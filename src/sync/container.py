"""Dependency injection container — creates shared instances."""

from sync.abstractions import Database
from sync.database import ConfigLoader, PooledDatabaseFactory, SchemaManager, TableConfigRepository, WatermarkRepository
from sync.database.mode import get_mode


_loader = ConfigLoader()
_factory = PooledDatabaseFactory()


def get_dest_db() -> Database:
    config = _loader.get_destination(get_mode())
    return _factory.get_or_create(f"dest_{get_mode()}", config, pool_size=5)


def get_source_db(name: str) -> Database:
    config = _loader.get_source(name)
    return _factory.get_or_create(f"source_{name}", config, pool_size=3)


def ensure_schema(db: Database):
    SchemaManager(db).ensure_tables()


def seed_config(db: Database):
    default_source = "local" if get_mode() == "local" else "mytdp_remote"
    TableConfigRepository(db).seed_initial_config(default_source=default_source)


def get_config_repo(db: Database) -> TableConfigRepository:
    return TableConfigRepository(db)


def get_watermark_repo(db: Database) -> WatermarkRepository:
    return WatermarkRepository(db)
