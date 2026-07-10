"""Core abstractions — protocols that define contracts.

Depend on these, never on concrete implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class Cursor(ABC):
    """Abstract cursor for database operations."""

    @abstractmethod
    def execute(self, sql: str, params: Optional[Tuple] = None) -> "Cursor": ...

    @abstractmethod
    def executemany(self, sql: str, params_list: List[Tuple]) -> None: ...

    @abstractmethod
    def fetchall(self) -> List[Dict[str, Any]]: ...

    @abstractmethod
    def fetchone(self) -> Optional[Dict[str, Any]]: ...

    @abstractmethod
    def close(self) -> None: ...


class Database(ABC):
    """Abstract database connection."""

    @abstractmethod
    def cursor(self) -> Cursor: ...

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...


class QueryBuilder(ABC):
    """Builds SQL queries for incremental sync."""

    @abstractmethod
    def build_select(self, config: dict, watermark: dict) -> Tuple[str, tuple]: ...

    @abstractmethod
    def build_upsert(self, config: dict) -> str: ...


class BatchWriter(ABC):
    """Writes rows to destination in transactional batches."""

    @abstractmethod
    def write(self, dest: Database, table: str, columns: List[str],
              rows: List[Dict[str, Any]], batch_size: int,
              upsert_sql: str) -> None: ...


class RetryPolicy(ABC):
    """Retries failed operations with backoff."""

    @abstractmethod
    def execute(self, func, *args, **kwargs) -> Any: ...


class StatusTracker(ABC):
    """Tracks live sync status per table."""

    @abstractmethod
    def mark_running(self, table_name: str) -> None: ...

    @abstractmethod
    def mark_success(self, table_name: str, rows: int, duration_ms: int) -> None: ...

    @abstractmethod
    def mark_error(self, table_name: str, error: str) -> None: ...


class SyncLogger(ABC):
    """Structured JSON logger for sync events."""

    @abstractmethod
    def sync_complete(self, rows: int, duration_ms: int) -> None: ...

    @abstractmethod
    def sync_error(self, error: str, attempt: int) -> None: ...

    @abstractmethod
    def no_data(self) -> None: ...

    @abstractmethod
    def watermark_update(self, ts: Any, id: Any) -> None: ...
