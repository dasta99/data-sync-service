# ─── Sync Database (backward compat) ──────────────────────────
from shared.connections import PooledDatabaseFactory, PyMySQLDatabase
from shared.config import ConfigLoader
from shared.repositories import SchemaManager, TableConfigRepository, WatermarkRepository

__all__ = [
    "PooledDatabaseFactory", "PyMySQLDatabase", "ConfigLoader",
    "SchemaManager", "TableConfigRepository", "WatermarkRepository",
]
