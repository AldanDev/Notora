from typing import Any, ClassVar, Literal

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from notora.v2.fastapi import make_admin_list_params_dep
from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.params import PaginationParams
from notora.v2.schemas.query import (
    PydanticFilterField,
    PydanticFiltersSchema,
    PydanticOrderBySchema,
    PydanticSortField,
)


class Box(GenericBaseModel):
    name: Mapped[str] = mapped_column(String)
    weight: Mapped[int] = mapped_column(Integer)


class BoxFilters(PydanticFiltersSchema[Box]):
    name: str | None = None
    weight_gte: int | None = None

    filter_fields: ClassVar[dict[str, PydanticFilterField[Any]]] = {
        'name':       PydanticFilterField(resolver=Box.name),
        'weight_gte': PydanticFilterField(resolver=Box.weight, operator='gte'),
    }


class BoxOrdering(PydanticOrderBySchema[Box]):
    order_by: Literal['name', 'weight'] | None = None
    direction: Literal['asc', 'desc'] = 'asc'

    sort_fields: ClassVar[dict[str, PydanticSortField[Any]]] = {
        'name':   PydanticSortField(resolver=Box.name),
        'weight': PydanticSortField(resolver=Box.weight),
    }


def test_builds_pagination_params_with_filters_and_ordering() -> None:
    dep = make_admin_list_params_dep(
        model=Box,
        filters_schema=BoxFilters,
        order_schema=BoxOrdering,
    )
    expected_limit = 30
    expected_offset = 60
    expected_filter_specs = 2
    expected_order_specs = 1
    params = dep(
        filters=BoxFilters(name='a', weight_gte=10),
        ordering=BoxOrdering(order_by='weight', direction='desc'),
        limit=expected_limit,
        offset=expected_offset,
    )
    assert isinstance(params, PaginationParams)
    assert params.limit == expected_limit
    assert params.offset == expected_offset
    assert params.filters is not None
    assert params.ordering is not None
    assert len(list(params.filters)) == expected_filter_specs
    assert len(list(params.ordering)) == expected_order_specs
    assert params.apply_default_filters is True


def test_empty_filters_and_ordering_produces_empty_specs() -> None:
    dep = make_admin_list_params_dep(
        model=Box,
        filters_schema=BoxFilters,
        order_schema=BoxOrdering,
    )
    default_limit = 20
    default_offset = 0
    params = dep(
        filters=BoxFilters(),
        ordering=BoxOrdering(),
        limit=default_limit,
        offset=default_offset,
    )
    assert list(params.filters or []) == []
    assert list(params.ordering or []) == []


def test_apply_default_filters_flag_propagates() -> None:
    dep = make_admin_list_params_dep(
        model=Box,
        filters_schema=BoxFilters,
        order_schema=BoxOrdering,
    )
    default_limit = 10
    default_offset = 0
    params = dep(
        filters=BoxFilters(),
        ordering=BoxOrdering(),
        limit=default_limit,
        offset=default_offset,
        apply_default_filters=False,
    )
    assert params.apply_default_filters is False
