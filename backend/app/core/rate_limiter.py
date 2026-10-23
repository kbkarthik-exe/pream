import time
from collections import defaultdict

from backend.app.core.config import settings
from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    """Thread-safe sliding window rate limiter keyed by IP and action."""

    def __init__(self) -> None:
        # key: (ip, action) -> list of timestamps
        self._records: dict[tuple[str, str], list[float]] = defaultdict(list)

    def check(self, request: Request, action: str, max_requests: int, window_seconds: int) -> None:
        if not settings.RATE_LIMIT_ENABLED:
            return

        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        key = (client_ip, action)

        # Filter out timestamps outside window
        cutoff = now - window_seconds
        timestamps = [ts for ts in self._records[key] if ts > cutoff]

        if len(timestamps) >= max_requests:
            oldest_relevant = timestamps[0]
            retry_after = max(1, int(window_seconds - (now - oldest_relevant)))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for {action}. Please try again in {retry_after}s.",
                headers={"Retry-After": str(retry_after)},
            )

        timestamps.append(now)
        self._records[key] = timestamps

    def reset(self) -> None:
        """Clear all rate limit records (useful for test suites)."""
        self._records.clear()


rate_limiter = InMemoryRateLimiter()
