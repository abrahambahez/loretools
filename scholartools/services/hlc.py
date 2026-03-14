from datetime import datetime, timezone

_counter: int = 0
_last_ms: int = 0


def now(peer_id: str) -> str:
    global _counter, _last_ms
    dt = datetime.now(timezone.utc)
    ms = int(dt.timestamp() * 1000)
    if ms == _last_ms:
        _counter += 1
    else:
        _last_ms = ms
        _counter = 1
    iso_utc = dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"
    return f"{iso_utc}-{_counter:04d}-{peer_id}"
