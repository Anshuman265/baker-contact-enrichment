"""Centralized sliding-window rate limiting for Enrich API requests."""

from __future__ import annotations

from collections import deque
import threading
import time
from collections.abc import Callable


class SlidingWindowRateLimiter:
    """Enforce both the safe burst and sustained Enrich request budgets."""

    def __init__(
        self,
        *,
        burst_limit: int = 20,
        sustained_limit: int = 240,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if burst_limit < 1 or sustained_limit < 1:
            raise ValueError("Rate limits must be positive integers.")
        self._burst_limit = burst_limit
        self._sustained_limit = sustained_limit
        self._clock = clock
        self._sleeper = sleeper
        self._requests: deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        """Block only until both rolling request windows allow one request."""
        while True:
            with self._lock:
                now = self._clock()
                self._discard_expired(now)
                one_second = [timestamp for timestamp in self._requests if timestamp > now - 1]
                if len(one_second) < self._burst_limit and len(self._requests) < self._sustained_limit:
                    self._requests.append(now)
                    return
                waits: list[float] = []
                if len(one_second) >= self._burst_limit:
                    waits.append(one_second[0] + 1 - now)
                if len(self._requests) >= self._sustained_limit:
                    waits.append(self._requests[0] + 60 - now)
                wait_for = max(min(waits), 0.001)
            self._sleeper(wait_for)

    def _discard_expired(self, now: float) -> None:
        while self._requests and self._requests[0] <= now - 60:
            self._requests.popleft()
