# ─── Sync Module (backward compat re-exports) ──────────────────
# This module re-exports from the new extract/transform/load/shared modules
# for backward compatibility with existing imports.

from shared.interfaces import Database, Cursor, QueryBuilder, RetryPolicy, StatusTracker, SyncLogger
from shared.config import ConfigLoader
from shared.connections import PooledDatabaseFactory, PyMySQLDatabase
from shared.repositories import SchemaManager, TableConfigRepository, WatermarkRepository
from shared.mode import set_mode, get_mode

__all__ = [
    "Database", "Cursor", "QueryBuilder", "RetryPolicy", "StatusTracker", "SyncLogger",
    "ConfigLoader", "PooledDatabaseFactory", "PyMySQLDatabase",
    "SchemaManager", "TableConfigRepository", "WatermarkRepository",
    "set_mode", "get_mode",
]
