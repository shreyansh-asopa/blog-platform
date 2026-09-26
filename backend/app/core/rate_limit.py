import time
from collections import deque
from collections.abc import Callable


class RateLimiter:
    """Allows at most `limit` hits per `window` seconds for each key (a "sliding window").

    Kept in the app's memory: simple and fast, but each server process counts on its
    own and the counts reset on restart. Running several processes would need a shared
    store such as Redis, with the same `hit` method.
    """

    _SWEEP_EVERY = 1000

    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._calls = 0

    def hit(self, key: str, limit: int, window: float) -> float | None:
        """Records a hit. Returns None if allowed, or how many seconds until one is allowed."""
        now = self._clock()
        self._calls += 1
        if self._calls % self._SWEEP_EVERY == 0:
            self._sweep(now, window)

        hits = self._hits.setdefault(key, deque())
        while hits and hits[0] <= now - window:
            hits.popleft()
        if len(hits) >= limit:
            return hits[0] + window - now
        hits.append(now)
        return None

    def _sweep(self, now: float, window: float) -> None:
        # Forget keys with no recent hits, so memory doesn't grow with every visitor ever seen
        stale = [key for key, hits in self._hits.items() if not hits or hits[-1] <= now - window]
        for key in stale:
            del self._hits[key]
