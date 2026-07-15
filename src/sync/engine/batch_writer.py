"""Transactional batch writer — backward compat redirect.

Use load.upsert.loader instead.
"""
from load.upsert.loader import TransactionalBatchWriter

__all__ = ["TransactionalBatchWriter"]
