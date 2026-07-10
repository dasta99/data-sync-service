"""HistoryLogger — appends to sync_history table and prunes old entries."""

from typing import Any, Dict, List

from sync.abstractions import Database


class HistoryLogger:
    """Appends to sync_history table, keeps last MAX_HISTORY runs."""

    MAX_HISTORY = 10

    def __init__(self, db: Database):
        self.db = db

    def log_success(self, table_name: str, rows: int, duration_ms: int) -> None:
        cur = self.db.cursor()
        try:
            cur.execute("""
                INSERT INTO sync_history
                    (table_name, status, rows_synced, duration_ms, started_at, completed_at)
                VALUES (%s, 'success', %s, %s, DATE_SUB(NOW(), INTERVAL %s SECOND), NOW())
            """, (table_name, rows, duration_ms, duration_ms // 1000))
        finally:
            cur.close()
        self._prune(table_name)
        self.db.commit()

    def log_error(self, table_name: str, error: str) -> None:
        cur = self.db.cursor()
        try:
            cur.execute("""
                INSERT INTO sync_history
                    (table_name, status, error_message, started_at, completed_at)
                VALUES (%s, 'error', %s, NOW(), NOW())
            """, (table_name, error))
        finally:
            cur.close()
        self.db.commit()

    def get_history(self, table_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        cur = self.db.cursor()
        try:
            cur.execute("""
                SELECT status, rows_synced, duration_ms, error_message,
                       started_at, completed_at
                FROM sync_history WHERE table_name = %s
                ORDER BY completed_at DESC LIMIT %s
            """, (table_name, limit))
            return cur.fetchall()
        finally:
            cur.close()

    def _prune(self, table_name: str) -> None:
        cur = self.db.cursor()
        try:
            cur.execute("""
                DELETE FROM sync_history WHERE table_name = %s
                AND id NOT IN (
                    SELECT id FROM (
                        SELECT id FROM sync_history WHERE table_name = %s
                        ORDER BY completed_at DESC LIMIT %s
                    ) AS recent
                )
            """, (table_name, table_name, self.MAX_HISTORY))
        finally:
            cur.close()
