"""StatusWriter — updates sync_status table (live state)."""

from typing import Any, Dict, List, Optional

from sync.abstractions import Database, StatusTracker


class StatusWriter(StatusTracker):
    """Updates the sync_status table."""

    def __init__(self, db: Database):
        self.db = db

    def mark_running(self, table_name: str) -> None:
        cur = self.db.cursor()
        try:
            cur.execute("""
                INSERT INTO sync_status (table_name, status, last_sync_at)
                VALUES (%s, 'running', NOW())
                ON DUPLICATE KEY UPDATE status = 'running'
            """, (table_name,))
        finally:
            cur.close()
        self.db.commit()

    def mark_success(self, table_name: str, rows: int, duration_ms: int) -> None:
        cur = self.db.cursor()
        try:
            cur.execute("""
                UPDATE sync_status SET
                    status = 'idle', last_sync_at = NOW(),
                    last_sync_duration_ms = %s, last_sync_rows = %s,
                    last_error = NULL, consecutive_errors = 0,
                    total_rows_synced = total_rows_synced + %s
                WHERE table_name = %s
            """, (duration_ms, rows, rows, table_name))
        finally:
            cur.close()
        self.db.commit()

    def mark_error(self, table_name: str, error: str) -> None:
        cur = self.db.cursor()
        try:
            cur.execute("""
                UPDATE sync_status SET
                    status = 'error', last_error = %s,
                    last_error_at = NOW(),
                    consecutive_errors = consecutive_errors + 1
                WHERE table_name = %s
            """, (error, table_name))
        finally:
            cur.close()
        self.db.commit()

    def get_all_status(self) -> List[Dict[str, Any]]:
        cur = self.db.cursor()
        try:
            cur.execute("SELECT * FROM sync_status ORDER BY last_sync_at DESC")
            return cur.fetchall()
        finally:
            cur.close()

    def get_table_status(self, table_name: str) -> Optional[Dict[str, Any]]:
        cur = self.db.cursor()
        try:
            cur.execute("SELECT * FROM sync_status WHERE table_name = %s", (table_name,))
            return cur.fetchone()
        finally:
            cur.close()
