"""Core abstractions — backward compat redirect.

Use shared.interfaces instead.
"""
from shared.interfaces import Database, Cursor, QueryBuilder, RetryPolicy, StatusTracker, SyncLogger

__all__ = ["Database", "Cursor", "QueryBuilder", "RetryPolicy", "StatusTracker", "SyncLogger"]
