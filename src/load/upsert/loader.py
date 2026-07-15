"""Transactional batch writer — upserts rows in batches."""

from typing import Any, Dict, List

from shared.interfaces import Database
from load.base import Loader


class TransactionalBatchWriter(Loader):
    """Writes rows in transactional batches with COMMIT/ROLLBACK."""

    def load(
        self,
        dest: Database,
        table: str,
        columns: List[str],
        rows: List[Dict[str, Any]],
        batch_size: int,
        upsert_sql: str,
    ) -> int:
        cur = dest.cursor()
        try:
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                values = [tuple(row[c] for c in columns) for row in batch]
                cur.executemany(upsert_sql, values)
            dest.commit()
            return len(rows)
        except Exception:
            dest.rollback()
            raise
        finally:
            cur.close()

    def write(
        self,
        dest: Database,
        table: str,
        columns: List[str],
        rows: List[Dict[str, Any]],
        batch_size: int,
        upsert_sql: str,
    ) -> None:
        """Legacy interface — same as load(), returns None."""
        self.load(dest, table, columns, rows, batch_size, upsert_sql)
