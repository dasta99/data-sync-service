"""Shared runtime mode — avoids circular imports between main and health."""

_current_mode = "prod"


def set_mode(mode: str):
    global _current_mode
    _current_mode = mode


def get_mode() -> str:
    return _current_mode
