"""Retry policy — simple retry with fixed delay."""

import time
from typing import Any

from shared.interfaces import RetryPolicy


class SimpleRetryPolicy(RetryPolicy):
    """Retries a function up to N times with a fixed delay."""

    def __init__(self, max_retries: int = 3, delay: float = 1.0):
        self.max_retries = max_retries
        self.delay = delay

    def execute(self, func, *args, **kwargs) -> Any:
        last_error = None
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay)
        raise last_error
