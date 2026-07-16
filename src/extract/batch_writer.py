"""Transactional batch writer."""

from typing import Any, Dict, List

from shared.interfaces import Database
from load.upsert.loader import TransactionalBatchWriter


__all__ = ["TransactionalBatchWriter"]
