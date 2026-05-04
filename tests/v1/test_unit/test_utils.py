from datetime import UTC, datetime

import pytest

from notora.utils.time import now_without_tz
from notora.utils.validation import validate_exclusive_presence


class TestNowWithoutTz:
    def test_returns_datetime_without_tzinfo(self) -> None:
        result = now_without_tz()
        assert isinstance(result, datetime)
        assert result.tzinfo is None

    def test_is_close_to_utc_now(self) -> None:
        before = datetime.now(UTC).replace(tzinfo=None)
        result = now_without_tz()
        after = datetime.now(UTC).replace(tzinfo=None)
        assert before <= result <= after

    def test_called_twice_is_non_decreasing(self) -> None:
        first = now_without_tz()
        second = now_without_tz()
        assert first <= second


class TestValidateExclusivePresence:
    def test_first_only_does_not_raise(self) -> None:
        validate_exclusive_presence('value', None)

    def test_second_only_does_not_raise(self) -> None:
        validate_exclusive_presence(None, 'value')

    def test_both_provided_raises(self) -> None:
        with pytest.raises(ValueError, match='Exactly one'):
            validate_exclusive_presence('a', 'b')

    def test_neither_provided_raises(self) -> None:
        with pytest.raises(ValueError, match='Exactly one'):
            validate_exclusive_presence(None, None)

    def test_falsy_non_none_first_counts_as_provided(self) -> None:
        # 0, '', [] are not None — should NOT raise
        validate_exclusive_presence(0, None)
        validate_exclusive_presence('', None)
        validate_exclusive_presence([], None)

    def test_falsy_non_none_both_raises(self) -> None:
        with pytest.raises(ValueError):
            validate_exclusive_presence(0, 0)

    def test_non_string_values_accepted(self) -> None:
        validate_exclusive_presence(42, None)
        validate_exclusive_presence(None, {'key': 'val'})
