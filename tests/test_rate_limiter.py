from baker_enrichment.rate_limiter import SlidingWindowRateLimiter


def test_rate_limiter_waits_for_burst_window() -> None:
    now = [0.0]
    waits: list[float] = []

    def sleep(seconds: float) -> None:
        waits.append(seconds)
        now[0] += seconds

    limiter = SlidingWindowRateLimiter(burst_limit=2, sustained_limit=10, clock=lambda: now[0], sleeper=sleep)
    limiter.acquire()
    limiter.acquire()
    limiter.acquire()
    assert waits == [1.0]


def test_rate_limiter_waits_for_sustained_window() -> None:
    now = [0.0]
    waits: list[float] = []

    def sleep(seconds: float) -> None:
        waits.append(seconds)
        now[0] += seconds

    limiter = SlidingWindowRateLimiter(burst_limit=10, sustained_limit=2, clock=lambda: now[0], sleeper=sleep)
    limiter.acquire()
    limiter.acquire()
    limiter.acquire()
    assert waits == [60.0]
