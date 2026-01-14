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
    meta = PaginationMetaSchema.calculate(total=0, limit=10, offset=0)
    assert meta.total == 0
    assert meta.current_page == 1
    assert meta.last_page == 1


def test_pagination_meta_clamps_current_page() -> None:
    current_page = 3
    last_page = 3
    meta = PaginationMetaSchema.calculate(total=5, limit=2, offset=10)
    assert meta.current_page == current_page
    assert meta.last_page == last_page
