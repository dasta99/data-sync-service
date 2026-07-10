"""Tests for adaptive polling — _compute_sleep_interval."""

import pytest
from sync.engine.loop import _compute_sleep_interval


class TestComputeSleepInterval:
    """Tests for the adaptive polling interval calculator."""

    def test_below_threshold_returns_base(self):
        """Before hitting threshold, always use base interval."""
        assert _compute_sleep_interval(30, 0, 2, 2, 600) == 30
        assert _compute_sleep_interval(30, 1, 2, 2, 600) == 30

    def test_at_threshold_returns_base(self):
        """At threshold, still base (backoff starts after threshold)."""
        assert _compute_sleep_interval(30, 2, 2, 2, 600) == 30

    def test_one_above_threshold_doubles(self):
        """First backoff: base × multiplier."""
        assert _compute_sleep_interval(30, 3, 2, 2, 600) == 60

    def test_two_above_threshold(self):
        """Second backoff: base × multiplier²."""
        assert _compute_sleep_interval(30, 4, 2, 2, 600) == 120

    def test_three_above_threshold(self):
        """Third backoff: base × multiplier³."""
        assert _compute_sleep_interval(30, 5, 2, 2, 600) == 240

    def test_hits_max_cap(self):
        """Backoff stops at max_poll_interval."""
        result = _compute_sleep_interval(30, 10, 2, 2, 600)
        assert result == 600

    def test_max_cap_not_exceeded(self):
        """Never exceeds max even with huge consecutive count."""
        result = _compute_sleep_interval(30, 100, 2, 2, 600)
        assert result == 600

    def test_multiplier_of_3(self):
        """With multiplier=3: 30 → 90 → 270 → 600 (capped)."""
        assert _compute_sleep_interval(30, 3, 2, 3, 600) == 90
        assert _compute_sleep_interval(30, 4, 2, 3, 600) == 270
        assert _compute_sleep_interval(30, 5, 2, 3, 600) == 600

    def test_high_threshold_delays_backoff(self):
        """With threshold=5, no backoff until 5 consecutive empty polls."""
        assert _compute_sleep_interval(30, 4, 5, 2, 600) == 30
        assert _compute_sleep_interval(30, 5, 5, 2, 600) == 30
        assert _compute_sleep_interval(30, 6, 5, 2, 600) == 60

    def test_zero_threshold_always_backs_off(self):
        """With threshold=0, start backing off immediately."""
        assert _compute_sleep_interval(30, 0, 0, 2, 600) == 30
        assert _compute_sleep_interval(30, 1, 0, 2, 600) == 60
        assert _compute_sleep_interval(30, 2, 0, 2, 600) == 120

    def test_large_base_interval(self):
        """60s base with multiplier 2: 60 → 120 → 240 → 480 → 600 (capped)."""
        assert _compute_sleep_interval(60, 3, 2, 2, 600) == 120
        assert _compute_sleep_interval(60, 4, 2, 2, 600) == 240
        assert _compute_sleep_interval(60, 5, 2, 2, 600) == 480
        assert _compute_sleep_interval(60, 6, 2, 2, 600) == 600
