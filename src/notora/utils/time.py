from datetime import UTC, datetime


def now_without_tz() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
