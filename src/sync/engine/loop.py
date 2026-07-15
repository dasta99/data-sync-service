"""Sync loops — backward compat redirect.

Use extract.loop instead.
"""
from extract.loop import run_sync_loop, sync_table, cancel_table, get_running_tables, get_cancelled_tables, _compute_sleep_interval

__all__ = ["run_sync_loop", "sync_table", "cancel_table", "get_running_tables", "get_cancelled_tables", "_compute_sleep_interval"]
