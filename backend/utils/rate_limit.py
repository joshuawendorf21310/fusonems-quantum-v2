from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone


_buckets = defaultdict(deque)


def check_rate_limit(bucket_key: str, limit: int, window_seconds: int = 60) -> bool:
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(seconds=window_seconds)
    bucket = _buckets[bucket_key]
    while bucket and bucket[0] < window_start:
        bucket.popleft()
    if len(bucket) >= limit:
        return False
    bucket.append(now)
    return True
