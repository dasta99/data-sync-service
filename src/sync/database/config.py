"""YAML config loader — backward compat redirect.

Use shared.config instead.
"""
from shared.config import ConfigLoader

__all__ = ["ConfigLoader"]
