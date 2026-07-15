"""Base transform handler protocol — defines the contract for all transforms."""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from shared.interfaces import Database
from shared.mode import get_mode

logger = logging.getLogger("transform")
local = get_mode() == "local"


@dataclass
class TransformResult:
    """Result of a transform operation."""
    handler_name: str
    rows_affected: int
    tables_written: List[str]
    duration_ms: int
    errors: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


class TransformHelper:
    """Mixin providing fetch/write/upsert helpers for transform handlers."""

    def fetch(self, db: Database, sql: str, params: tuple) -> list:
        """Run a SELECT against source DB. Returns list of dicts."""
        cur = db.cursor()
        try:
            t0 = time.time()
            cur.execute(sql, params)
            rows = cur.fetchall()
            ms = int((time.time() - t0) * 1000)
            if local:
                preview = " ".join(sql.split())[:120]
                logger.info(f"    query: {preview}...")
                logger.info(f"    params: {params} → {len(rows)} rows in {ms}ms")
                if rows:
                    logger.info(f"    sample: {dict(rows[0])}")
            return rows
        finally:
            cur.close()

    def write(self, db: Database, sql: str, params_list: list) -> None:
        """Bulk upsert into destination DB."""
        cur = db.cursor()
        try:
            t0 = time.time()
            cur.executemany(sql, params_list)
            ms = int((time.time() - t0) * 1000)
            if local:
                logger.info(f"    write: {len(params_list)} rows in {ms}ms")
        finally:
            cur.close()

    def run_transform(
        self,
        name: str,
        source_db: Database,
        dest_db: Database,
        sql: str,
        params: tuple,
        map_row: Callable[[dict], tuple],
        upsert_sql: str,
    ) -> int:
        """Run a full transform: fetch → map → write. Returns rows written."""
        rows = self.fetch(source_db, sql, params)
        if not rows:
            return 0
        params_list = [map_row(r) for r in rows]
        self.write(dest_db, upsert_sql, params_list)
        if local:
            logger.info(f"  {name}: {len(rows)} rows")
        return len(rows)

    @staticmethod
    def make_upsert(table: str, columns: List[str], pk: str = None) -> str:
        """Generate INSERT ... ON DUPLICATE KEY UPDATE SQL from column list.

        Args:
            table: Destination table name
            columns: All columns including PKs
            pk: Primary key column(s) — if None, uses first column.
                 Pass empty string '' to skip ON DUPLICATE KEY.
        """
        if pk is None:
            pk = columns[0]

        placeholders = ", ".join(["%s"] * len(columns))
        col_list = ", ".join(columns)

        if pk == "":
            return f"INSERT IGNORE INTO {table} ({col_list}) VALUES ({placeholders})"

        update_cols = [c for c in columns if c not in pk.split(",")]
        update_clause = ", ".join(f"{c}=VALUES({c})" for c in update_cols)
        return f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {update_clause}"

    @staticmethod
    def vals(rows: list, *keys: str) -> list:
        """Extract values from dict rows in key order.

        Usage:
            params_list = self.vals(rows, "sid", "name", "total")
        """
        return [tuple(row[k] for k in keys) for row in rows]


class TransformHandler(ABC, TransformHelper):
    """Base protocol for transform phase handlers.

    Each handler:
    1. Reads from staging tables (already synced by extract)
    2. Transforms/aggregates the data
    3. Writes to fact/mart tables via loaders

    Inherits TransformHelper for fetch/write/upsert convenience methods.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique handler name (e.g., 'sir', 'rally')."""
        ...

    @property
    @abstractmethod
    def depends_on(self) -> List[str]:
        """List of source table names that must be synced before this handler runs."""
        ...

    @property
    @abstractmethod
    def outputs(self) -> List[str]:
        """List of destination tables this handler writes to."""
        ...

    @abstractmethod
    def transform(
        self,
        source_db: Database,
        dest_db: Database,
        params: Optional[Dict[str, Any]] = None,
    ) -> TransformResult:
        """Execute the transform. Returns result with rows affected and any errors."""
        ...

    def should_run(self, last_sync_times: Dict[str, Any], last_transform_time: Optional[Any]) -> bool:
        """Determine if this handler should run based on sync/transform timestamps.

        Default: run if any dependency synced after last transform.
        Override for custom logic.
        """
        if last_transform_time is None:
            return True
        for dep_table in self.depends_on:
            dep_time = last_sync_times.get(dep_table)
            if dep_time and dep_time > last_transform_time:
                return True
        return False
