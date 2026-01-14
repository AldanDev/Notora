import pytest

from notora.v2.schemas.base import PaginationMetaSchema


@pytest.mark.parametrize('limit', [0, -1])
def test_pagination_meta_rejects_non_positive_limit(limit: int) -> None:
    with pytest.raises(ValueError, match='limit must be a positive integer'):
        PaginationMetaSchema.calculate(total=10, limit=limit, offset=0)


@pytest.mark.parametrize('offset', [-1, -10])
def test_pagination_meta_rejects_negative_offset(offset: int) -> None:
    with pytest.raises(ValueError, match='offset must be zero or a positive integer'):
        PaginationMetaSchema.calculate(total=10, limit=5, offset=offset)


def test_pagination_meta_zero_total_is_single_page() -> None:
    total = 0
    limit = 10
    offset = 0
    meta = PaginationMetaSchema.calculate(total=total, limit=limit, offset=offset)
    assert meta.total == total
    assert meta.limit == limit
    assert meta.offset == offset


def test_pagination_meta_retains_offset_and_total() -> None:
    total = 5
    limit = 2
    offset = 10
    meta = PaginationMetaSchema.calculate(total=total, limit=limit, offset=offset)
    assert meta.total == total
    assert meta.limit == limit
    assert meta.offset == offset
