"""Transform orchestrator — dispatches handlers when dependencies are met."""

import logging
import time
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from shared.interfaces import Database
from shared.mode import get_mode
from transform.registry import get_all_handlers, get_handler, discover_handlers
from transform.dependencies import DependencyGraph
from transform.base import TransformResult

logger = logging.getLogger("transform.orchestrator")
local = get_mode() == "local"


class TransformOrchestrator:
    """Coordinates transform handlers based on dependency readiness.

    Called by extract loop after each table sync completes.
    Checks if any handlers are now ready to run.
    """

    def __init__(self, dest_db: Database, source_db_factory: Optional[Callable[[str], Database]] = None, default_source: str = "mytdp_remote"):
        self.dest_db = dest_db
        self.source_db_factory = source_db_factory
        self.default_source = default_source
        self.graph = DependencyGraph()
        self._initialized = False

    def initialize(self):
        """Discover handlers and build dependency graph."""
        if self._initialized:
            return

        discover_handlers()

        for name, handler in get_all_handlers().items():
            self.graph.register_handler(name, handler.depends_on)
            logger.info(f"Registered handler '{name}' with deps: {handler.depends_on}")

        self._initialized = True

    def notify(self, table_name: str, rows_synced: int):
        """Called by extract loop after a table sync completes.

        Updates the graph and runs any ready handlers.
        """
        if not self._initialized:
            self.initialize()

        self.graph.update_table_sync(table_name, datetime.utcnow())
        logger.info(f"Table '{table_name}' synced ({rows_synced} rows), checking handlers...")

        ready = self.graph.get_ready_handlers()
        if not ready:
            logger.debug(f"No handlers ready after '{table_name}' sync")
            return

        for handler_name in ready:
            self._run_handler(handler_name)

    def _run_handler(self, handler_name: str):
        """Execute a single transform handler."""
        handler = get_handler(handler_name)
        if not handler:
            logger.error(f"Handler '{handler_name}' not found in registry")
            return

        logger.info(f"Running transform handler: {handler_name}")
        start_time = time.time()

        try:
            # Get source DB for this handler (handlers may need to read from source)
            source_db = None
            if self.source_db_factory:
                source_db = self.source_db_factory(self.default_source)
                if local:
                    logger.info(f"  source: {self.default_source}")

            result = handler.transform(
                source_db=source_db,
                dest_db=self.dest_db,
            )
            duration_ms = int((time.time() - start_time) * 1000)

            self.graph.update_handler_run(handler_name, datetime.utcnow())

            if result.success:
                logger.info(
                    f"Handler '{handler_name}' completed: "
                    f"{result.rows_affected} rows, {result.tables_written}, "
                    f"{duration_ms}ms"
                )
            else:
                logger.error(
                    f"Handler '{handler_name}' completed with errors: "
                    f"{result.errors}"
                )

        except Exception as e:
            logger.error(f"Handler '{handler_name}' failed: {e}")
            raise

    def force_run(self, handler_name: str):
        """Force-run a handler regardless of dependency state."""
        if not self._initialized:
            self.initialize()
        self._run_handler(handler_name)

    def status(self) -> dict:
        """Return orchestrator status for API/debugging."""
        if not self._initialized:
            self.initialize()
        return self.graph.snapshot()
