"""Per-user rate limiting for endpoints that dispatch paid ingestion work."""

import time
import uuid
from collections import defaultdict, deque

from fastapi import Depends, HTTPException

from app.modules.auth.models import User
from app.modules.auth.service import get_current_user


class UserRateLimiter:
    """Sliding-window limiter keyed on the authenticated user id.

    Use one instance as a FastAPI dependency (``dependencies=[Depends(limiter)]``)
    on every endpoint that should share the same budget.

    ponytail: in-memory, so per-process. Fine while the API runs a single
    Cloud Run instance; if the API scales out, move the window to the
    existing Upstash Redis so all instances share one count.
    """

    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[uuid.UUID, deque[float]] = defaultdict(deque)

    async def __call__(self, current_user: User = Depends(get_current_user)) -> None:
        now = time.monotonic()
        hits = self._hits[current_user.id]
        while hits and now - hits[0] >= self.window_seconds:
            hits.popleft()
        if len(hits) >= self.limit:
            retry_after = (
                int(self.window_seconds - (now - hits[0])) + 1 if hits else 1
            )
            raise HTTPException(
                status_code=429,
                detail="Too many ingestion requests; try again shortly",
                headers={"Retry-After": str(retry_after)},
            )
        hits.append(now)
