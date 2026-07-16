"""Base loader protocol — defines the contract for all loaders."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from shared.interfaces import Database


class Loader(ABC):
    """Base protocol for load phase strategies."""

    @abstractmethod
    def load(
        self,
        dest: Database,
        table: str,
        columns: List[str],
        rows: List[Dict[str, Any]],
        batch_size: int,
        upsert_sql: str,
    ) -> int:
        """Load rows into destination. Returns rows loaded."""
        ...
