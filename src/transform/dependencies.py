"""Dependency graph — tracks which tables a handler needs and when to fire."""

from typing import Dict, List, Set, Optional
from datetime import datetime


class DependencyGraph:
    """Manages dependency tracking for transform handlers.

    For each handler, tracks:
    - Which source tables it depends on
    - When each source table was last synced
    - When the handler last ran
    - Whether all deps are satisfied
    """

    def __init__(self):
        # handler_name -> [dep_table_names]
        self._handler_deps: Dict[str, List[str]] = {}
        # table_name -> last_synced_at
        self._table_sync_times: Dict[str, datetime] = {}
        # handler_name -> last_triggered_at
        self._handler_run_times: Dict[str, datetime] = {}

    def register_handler(self, handler_name: str, depends_on: List[str]):
        """Register a handler and its dependencies."""
        self._handler_deps[handler_name] = depends_on

    def update_table_sync(self, table_name: str, synced_at: Optional[datetime] = None):
        """Record that a source table was just synced."""
        self._table_sync_times[table_name] = synced_at or datetime.utcnow()

    def update_handler_run(self, handler_name: str, run_at: Optional[datetime] = None):
        """Record that a handler just ran."""
        self._handler_run_times[handler_name] = run_at or datetime.utcnow()

    def get_last_sync_time(self, table_name: str) -> Optional[datetime]:
        return self._table_sync_times.get(table_name)

    def get_last_run_time(self, handler_name: str) -> Optional[datetime]:
        return self._handler_run_times.get(handler_name)

    def is_ready(self, handler_name: str) -> bool:
        """Check if all dependencies for a handler are satisfied.

        Ready = every dep table synced after the handler last ran.
        """
        deps = self._handler_deps.get(handler_name, [])
        if not deps:
            return False

        last_run = self._handler_run_times.get(handler_name)

        for dep in deps:
            sync_time = self._table_sync_times.get(dep)
            if sync_time is None:
                return False  # dep never synced
            if last_run and sync_time <= last_run:
                return False  # dep synced before last run

        return True

    def get_ready_handlers(self) -> List[str]:
        """Return all handler names whose deps are satisfied."""
        return [name for name in self._handler_deps if self.is_ready(name)]

    def get_pending_deps(self, handler_name: str) -> Dict[str, bool]:
        """Return {dep_table: is_synced} for debugging."""
        deps = self._handler_deps.get(handler_name, [])
        last_run = self._handler_run_times.get(handler_name)
        result = {}
        for dep in deps:
            sync_time = self._table_sync_times.get(dep)
            if sync_time is None:
                result[dep] = False
            elif last_run and sync_time <= last_run:
                result[dep] = False
            else:
                result[dep] = True
        return result

    def snapshot(self) -> dict:
        """Return full state for debugging/API."""
        return {
            "handlers": dict(self._handler_deps),
            "table_sync_times": {k: str(v) for k, v in self._table_sync_times.items()},
            "handler_run_times": {k: str(v) for k, v in self._handler_run_times.items()},
            "ready": self.get_ready_handlers(),
        }
