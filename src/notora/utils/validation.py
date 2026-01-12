from typing import Any


def validate_exclusive_presence(first: Any | None, second: Any | None) -> None:
    """Validates that exactly one of `first` or `second` is provided.

    Raises a ValueError if none or both are provided.

    Args:
        first: The first value to check.
        second: The second value to check.

    """
    is_first = first is not None
    is_second = second is not None
    if is_first == is_second:  # Both are True or both are False
        msg = 'Exactly one of arguments must be provided, but not both.'
        raise ValueError(msg)
