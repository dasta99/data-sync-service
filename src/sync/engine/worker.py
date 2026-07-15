"""Base sync worker — backward compat redirect.

Use extract.worker instead.
"""
from extract.worker import BaseSyncWorker

__all__ = ["BaseSyncWorker"]
