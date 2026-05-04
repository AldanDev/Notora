from datetime import UTC, datetime

import pytest

from notora.utils.time import now_without_tz
from notora.utils.validation import validate_exclusive_presence


def test_now_without_tz_returns_datetime_without_tzinfo() -> None:
    result = now_without_tz()
    assert isinstance(result, datetime)
    assert result.tzinfo is None


def test_now_without_tz_is_close_to_utc_now() -> None:
    before = datetime.now(UTC).replace(tzinfo=None)
    result = now_without_tz()
    after = datetime.now(UTC).replace(tzinfo=None)
    assert before <= result <= after


def test_now_without_tz_called_twice_is_non_decreasing() -> None:
    first = now_without_tz()
    second = now_without_tz()
    assert first <= second


def test_validate_exclusive_presence_first_only_does_not_raise() -> None:
    validate_exclusive_presence('value', None)


def test_validate_exclusive_presence_second_only_does_not_raise() -> None:
    validate_exclusive_presence(None, 'value')


def test_validate_exclusive_presence_both_provided_raises() -> None:
    with pytest.raises(ValueError, match='Exactly one'):
        validate_exclusive_presence('a', 'b')


def test_validate_exclusive_presence_neither_provided_raises() -> None:
    with pytest.raises(ValueError, match='Exactly one'):
        validate_exclusive_presence(None, None)


def test_validate_exclusive_presence_falsy_non_none_first_counts_as_provided() -> None:
    # 0, '', [] are not None — should NOT raise
    validate_exclusive_presence(0, None)
    validate_exclusive_presence('', None)
    validate_exclusive_presence([], None)


def test_validate_exclusive_presence_falsy_non_none_both_raises() -> None:
    with pytest.raises(ValueError):
        validate_exclusive_presence(0, 0)


def test_validate_exclusive_presence_non_string_values_accepted() -> None:
    validate_exclusive_presence(42, None)
    validate_exclusive_presence(None, {'key': 'val'})
