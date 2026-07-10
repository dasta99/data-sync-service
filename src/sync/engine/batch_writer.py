"""Transactional batch writer."""

from typing import Any, Dict, List

from sync.abstractions import BatchWriter, Database


class TransactionalBatchWriter(BatchWriter):
    """Writes rows in transactional batches with COMMIT/ROLLBACK."""

    def write(self, dest: Database, table: str, columns: List[str],
              rows: List[Dict[str, Any]], batch_size: int,
              upsert_sql: str) -> None:
        cur = dest.cursor()
        try:
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                values = [tuple(row[c] for c in columns) for row in batch]
                cur.executemany(upsert_sql, values)
            dest.commit()
        except Exception:
            dest.rollback()
            raise
        finally:
            cur.close()
