"""Structured JSON logger — backward compat redirect.

Use extract.logger instead.
"""
from extract.logger import SyncJsonLogger

__all__ = ["SyncJsonLogger"]
