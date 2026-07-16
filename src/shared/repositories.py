"""Data repositories — schema, config CRUD, watermarks."""

import json
from typing import Any, Dict, List, Optional

from shared.interfaces import Database


class SchemaManager:
    """Creates sync_config, sync_status, sync_history tables."""

    def __init__(self, db: Database):
        self.db = db

    def ensure_tables(self):
        for ddl in [_SYNC_CONFIG_DDL, _SYNC_STATUS_DDL, _SYNC_HISTORY_DDL]:
            cur = self.db.cursor()
            try:
                cur.execute(ddl)
            finally:
                cur.close()


class TableConfigRepository:
    """Read/write sync_config table."""

    def __init__(self, db: Database):
        self.db = db

    def get_enabled_tables(self) -> List[Dict[str, Any]]:
        cur = self.db.cursor()
        try:
            cur.execute("SELECT * FROM sync_config WHERE enabled = 1")
            return [self._parse(r) for r in cur.fetchall()]
        finally:
            cur.close()

    def get_table_config(self, name: str) -> Optional[Dict[str, Any]]:
        cur = self.db.cursor()
        try:
            cur.execute("SELECT * FROM sync_config WHERE table_name = %s", (name,))
            row = cur.fetchone()
            return self._parse(row) if row else None
        finally:
            cur.close()

    def get_all_tables(self) -> List[Dict[str, Any]]:
        cur = self.db.cursor()
        try:
            cur.execute("SELECT * FROM sync_config ORDER BY table_name")
            return [self._parse(r) for r in cur.fetchall()]
        finally:
            cur.close()

    def create(self, config: Dict[str, Any]) -> Dict[str, Any]:
        cur = self.db.cursor()
        try:
            cur.execute(_CREATE_SQL, (
                config["table_name"],
                config["source_name"],
                config["source_table"],
                config["dest_table"],
                config.get("enabled", True),
                config.get("poll_interval", 30),
                config.get("batch_size", 500),
                config.get("watermark_column", "updated_at"),
                config.get("primary_key", "id"),
                json.dumps(config.get("columns", [])),
                json.dumps(config.get("filters", [])),
                config.get("timezone_offset", 0),
                config.get("no_data_threshold", 2),
                config.get("backoff_multiplier", 2),
                config.get("max_poll_interval", 600),
            ))
        finally:
            cur.close()
        self.db.commit()
        return self.get_table_config(config["table_name"])

    def update(self, name: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not fields:
            return self.get_table_config(name)

        set_parts = []
        values = []
        for key, val in fields.items():
            if key in _UPDATABLE_FIELDS:
                set_parts.append(f"{key} = %s")
                if key in ("columns", "filters") and isinstance(val, list):
                    values.append(json.dumps(val))
                else:
                    values.append(val)

        if not set_parts:
            return self.get_table_config(name)

        values.append(name)
        sql = f"UPDATE sync_config SET {', '.join(set_parts)} WHERE table_name = %s"
        cur = self.db.cursor()
        try:
            cur.execute(sql, tuple(values))
        finally:
            cur.close()
        self.db.commit()
        return self.get_table_config(name)

    def delete(self, name: str) -> bool:
        cur = self.db.cursor()
        try:
            cur.execute("DELETE FROM sync_config WHERE table_name = %s", (name,))
            deleted = cur.rowcount > 0
        finally:
            cur.close()
        self.db.commit()
        return deleted

    def seed_initial_config(self, default_source: str = "mytdp_remote"):
        cur = self.db.cursor()
        try:
            cur.execute("SELECT COUNT(*) as cnt FROM sync_config")
            if cur.fetchone()["cnt"] > 0:
                return
        finally:
            cur.close()

        cur = self.db.cursor()
        try:
            cur.execute(_SEED_SQL, (
                "booth_voter", default_source, "booth_voter", "booth_voter",
                30, 500, "updated_at", "id",
                json.dumps(["id","booth_id","assembly_id","parliament_id","voter_id",
                    "serial_no","kss_id","sir_verified","form_submitted_to_blo",
                    "blo_digitized","sir_verified_by","sir_verified_role",
                    "sir_caste_category","sir_political_party_id","sir_caste_id",
                    "is_enumiration_form_submitted","sir_mobile_number",
                    "sir_latitude","sir_longitude","file_path","sir_status",
                    "created_at","updated_at","positive"]),
                json.dumps(["sir_verified = 1"]),
                330,
            ))
        finally:
            cur.close()
        self.db.commit()

    @staticmethod
    def _parse(row: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "table_name": row["table_name"],
            "source_name": row["source_name"],
            "source_table": row["source_table"],
            "dest_table": row["dest_table"],
            "enabled": bool(row["enabled"]),
            "poll_interval": row["poll_interval"],
            "batch_size": row["batch_size"],
            "watermark_column": row["watermark_column"],
            "primary_key": row["primary_key"],
            "columns": json.loads(row["columns_json"]) if row["columns_json"] else [],
            "filters": json.loads(row["filters_json"]) if row["filters_json"] else [],
            "timezone_offset": row["timezone_offset"],
            "no_data_threshold": row.get("no_data_threshold") or 2,
            "backoff_multiplier": row.get("backoff_multiplier") or 2,
            "max_poll_interval": row.get("max_poll_interval") or 600,
        }


class WatermarkRepository:
    """Read/write watermark (last_synced_at, last_record_id)."""

    def __init__(self, db: Database):
        self.db = db

    def get_watermark(self, table_name: str) -> Dict[str, Any]:
        cur = self.db.cursor()
        try:
            cur.execute(
                "SELECT last_synced_at, last_record_id, watermark_column "
                "FROM sync_config WHERE table_name = %s",
                (table_name,),
            )
            row = cur.fetchone()
        finally:
            cur.close()

        if row and row["last_synced_at"]:
            return {
                "last_timestamp": row["last_synced_at"],
                "last_id": row["last_record_id"] or "0",
            }
        # Use 0 as default when watermark_column is not a timestamp column
        wm_col = row["watermark_column"] if row else "updated_at"
        default_ts = "1970-01-01 00:00:00" if wm_col != "id" else "0"
        return {"last_timestamp": default_ts, "last_id": "0"}

    def update_watermark(self, table_name: str, last_ts: Any, last_id: Any):
        cur = self.db.cursor()
        try:
            cur.execute(
                "UPDATE sync_config SET last_synced_at = %s, last_record_id = %s "
                "WHERE table_name = %s",
                (str(last_ts), str(last_id), table_name),
            )
        finally:
            cur.close()
        self.db.commit()


# ─── SQL Constants ────────────────────────────────────────────

_UPDATABLE_FIELDS = {
    "source_name", "source_table", "dest_table", "enabled",
    "poll_interval", "batch_size", "watermark_column", "primary_key",
    "columns", "filters", "timezone_offset",
    "no_data_threshold", "backoff_multiplier", "max_poll_interval",
}

_SEED_SQL = """
INSERT INTO sync_config
    (table_name, source_name, source_table, dest_table,
     enabled, poll_interval, batch_size, watermark_column,
     primary_key, columns_json, filters_json, timezone_offset)
VALUES (%s, %s, %s, %s, 1, %s, %s, %s, %s, %s, %s, %s)
"""

_CREATE_SQL = """
INSERT INTO sync_config
    (table_name, source_name, source_table, dest_table,
     enabled, poll_interval, batch_size, watermark_column,
     primary_key, columns_json, filters_json, timezone_offset,
     no_data_threshold, backoff_multiplier, max_poll_interval)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

_SYNC_CONFIG_DDL = """
CREATE TABLE IF NOT EXISTS sync_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(100) UNIQUE NOT NULL,
    source_name VARCHAR(100) NOT NULL,
    source_table VARCHAR(100) NOT NULL,
    dest_table VARCHAR(100) NOT NULL,
    enabled TINYINT(1) DEFAULT 1,
    poll_interval INT DEFAULT 30,
    batch_size INT DEFAULT 500,
    watermark_column VARCHAR(100) DEFAULT 'updated_at',
    primary_key VARCHAR(100) DEFAULT 'id',
    columns_json TEXT,
    filters_json TEXT,
    timezone_offset INT DEFAULT 0,
    no_data_threshold INT DEFAULT 2,
    backoff_multiplier INT DEFAULT 2,
    max_poll_interval INT DEFAULT 600,
    last_synced_at DATETIME DEFAULT NULL,
    last_record_id VARCHAR(100) DEFAULT NULL,
    inserted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)
"""

_SYNC_STATUS_DDL = """
CREATE TABLE IF NOT EXISTS sync_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(100) UNIQUE NOT NULL,
    status ENUM('running','idle','error','disabled') DEFAULT 'idle',
    last_sync_at DATETIME DEFAULT NULL,
    last_sync_duration_ms INT DEFAULT NULL,
    last_sync_rows INT DEFAULT NULL,
    last_error TEXT DEFAULT NULL,
    last_error_at DATETIME DEFAULT NULL,
    consecutive_errors INT DEFAULT 0,
    total_rows_synced BIGINT DEFAULT 0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)
"""

_SYNC_HISTORY_DDL = """
CREATE TABLE IF NOT EXISTS sync_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    status ENUM('success','error') NOT NULL,
    rows_synced INT DEFAULT 0,
    duration_ms INT DEFAULT 0,
    error_message TEXT DEFAULT NULL,
    started_at DATETIME NOT NULL,
    completed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_history_table (table_name, completed_at DESC)
)
"""
