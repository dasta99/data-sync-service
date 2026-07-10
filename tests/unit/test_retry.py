"""Tests for SimpleRetryPolicy."""

import pytest
from sync.engine.retry import SimpleRetryPolicy


@pytest.fixture
def policy():
    return SimpleRetryPolicy(max_retries=3, delay=0.01)


class TestRetryPolicy:
    def test_success_on_first_attempt(self, policy):
        func = lambda: "ok"
        assert policy.execute(func) == "ok"

    def test_success_after_retries(self, policy):
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("not yet")
            return "done"

        assert policy.execute(flaky) == "done"
        assert call_count == 3

    def test_raises_after_max_retries(self, policy):
        def always_fail():
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            policy.execute(always_fail)

    def test_passes_args_and_kwargs(self, policy):
        def add(a, b, c=0):
            return a + b + c

        assert policy.execute(add, 1, 2, c=3) == 6

    def test_max_retries_1_no_retry(self):
        policy = SimpleRetryPolicy(max_retries=1, delay=0.01)

        def fail():
            raise ValueError("no retry")

        with pytest.raises(ValueError):
            policy.execute(fail)

    def test_delay_between_retries(self):
        import time
        policy = SimpleRetryPolicy(max_retries=2, delay=0.05)
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("first")
            return "ok"

        start = time.time()
        result = policy.execute(flaky)
        elapsed = time.time() - start

        assert result == "ok"
        assert elapsed >= 0.05  # at least one delay
