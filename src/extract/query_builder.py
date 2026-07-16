"""Keyset pagination query builder."""

from typing import Tuple

from shared.interfaces import QueryBuilder


class KeysetQueryBuilder(QueryBuilder):
    """Builds queries: (updated_at > X OR (updated_at = X AND id > Y))."""

    def build_select(self, config: dict, watermark: dict) -> Tuple[str, tuple]:
        cols = ", ".join(config["columns"])
        table = config["source_table"]
        wm_col = config["watermark_column"]
        pk = config["primary_key"]
        batch = config["batch_size"]

        condition = f"({wm_col} > %s OR ({wm_col} = %s AND {pk} > %s))"

        filter_clauses = ""
        for f in config.get("filters", []):
            if f.strip():
                filter_clauses += f" AND {f}"

        query = f"""
            SELECT {cols}
            FROM {table}
            WHERE {condition} {filter_clauses}
            ORDER BY {wm_col}, {pk}
            LIMIT {batch}
        """
        params = (watermark["last_timestamp"], watermark["last_timestamp"], watermark["last_id"])
        return query, params

    def build_upsert(self, config: dict) -> str:
        table = config["dest_table"]
        pk = config["primary_key"]
        cols = config["columns"]

        update_cols = [c for c in cols if c != pk]
        col_list = ", ".join(cols)
        placeholders = ", ".join(["%s"] * len(cols))

        if update_cols:
            update_clause = ", ".join(f"{c} = VALUES({c})" for c in update_cols)
            return f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {update_clause}"
        return f"INSERT IGNORE INTO {table} ({col_list}) VALUES ({placeholders})"
