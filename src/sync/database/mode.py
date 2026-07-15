"""Shared runtime mode — backward compat redirect.

Use shared.mode instead.
"""
from shared.mode import set_mode, get_mode

__all__ = ["set_mode", "get_mode"]
