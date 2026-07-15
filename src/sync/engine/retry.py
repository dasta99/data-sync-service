"""Retry policy — backward compat redirect.

Use extract.retry instead.
"""
from extract.retry import SimpleRetryPolicy

__all__ = ["SimpleRetryPolicy"]
