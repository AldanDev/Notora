from typing import Any, ClassVar, Literal

import pytest

pytest.importorskip('fastapi')

from fastapi.dependencies.utils import get_dependant  # pyright: ignore[reportMissingImports]
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from notora.v2.fastapi import make_list_params_dependency
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
        'name': PydanticFilterField(resolver=Box.name),
        'weight_gte': PydanticFilterField(resolver=Box.weight, operator='gte'),
    }


class BoxOrdering(PydanticOrderBySchema[Box]):
    order_by: Literal['name', 'weight'] | None = None
    direction: Literal['asc', 'desc'] = 'asc'

    sort_fields: ClassVar[dict[str, PydanticSortField[Any]]] = {
        'name': PydanticSortField(resolver=Box.name),
        'weight': PydanticSortField(resolver=Box.weight),
    }


def _build_base_dep() -> Any:
    return make_list_params_dependency(
        model=Box,
        filters_schema=BoxFilters,
        order_schema=BoxOrdering,
    )


def _get_limit_le(dep: Any) -> list[Any]:
    """Pull the ``Le(...)`` constraint (if any) off the ``limit`` query param."""
    dependant = get_dependant(path='/', call=dep)
    limit_param = next(p for p in dependant.query_params if p.name == 'limit')
    metadata = getattr(limit_param.field_info, 'metadata', [])
    return [m for m in metadata if hasattr(m, 'le')]


def test_builds_pagination_params_with_filters_and_ordering() -> None:
    dep = _build_base_dep()
    limit = 30
    offset = 60
    expected_filter_specs = 2
    expected_order_specs = 1
    params = dep(
        filters=BoxFilters(name='a', weight_gte=10),
        ordering=BoxOrdering(order_by='weight', direction='desc'),
        limit=limit,
        offset=offset,
    )
    assert isinstance(params, PaginationParams)
    assert params.limit == limit
    assert params.offset == offset
    assert params.filters is not None
    assert params.ordering is not None
    assert len(list(params.filters)) == expected_filter_specs
    assert len(list(params.ordering)) == expected_order_specs
    assert params.apply_default_filters is True


def test_empty_filters_and_ordering_produces_empty_specs() -> None:
    dep = _build_base_dep()
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


def test_bypass_param_not_configured_keeps_apply_default_filters_true() -> None:
    """When default_filter_bypass_param is not configured, the bypass path is absent and apply_default_filters stays True."""
    dep = _build_base_dep()
    default_limit = 10
    default_offset = 0
    params = dep(
        filters=BoxFilters(),
        ordering=BoxOrdering(),
        limit=default_limit,
        offset=default_offset,
    )
    assert params.apply_default_filters is True


def test_bypass_param_false_keeps_apply_default_filters_true() -> None:
    dep = make_list_params_dependency(
        model=Box,
        filters_schema=BoxFilters,
        order_schema=BoxOrdering,
        default_filter_bypass_param='show_deleted',
    )
    default_limit = 10
    default_offset = 0
    params = dep(
        filters=BoxFilters(),
        ordering=BoxOrdering(),
        limit=default_limit,
        offset=default_offset,
        bypass_default_filters=False,
    )
    assert params.apply_default_filters is True


def test_bypass_param_true_flips_apply_default_filters_false() -> None:
    dep = make_list_params_dependency(
        model=Box,
        filters_schema=BoxFilters,
        order_schema=BoxOrdering,
        default_filter_bypass_param='show_deleted',
    )
    default_limit = 10
    default_offset = 0
    params = dep(
        filters=BoxFilters(),
        ordering=BoxOrdering(),
        limit=default_limit,
        offset=default_offset,
        bypass_default_filters=True,
    )
    assert params.apply_default_filters is False


def test_bypass_param_exposes_alias_to_fastapi() -> None:
    """Inner param name is fixed (``bypass_default_filters``); FastAPI publishes the alias."""
    dep = make_list_params_dependency(
        model=Box,
        filters_schema=BoxFilters,
        order_schema=BoxOrdering,
        default_filter_bypass_param='show_deleted',
    )
    dependant = get_dependant(path='/', call=dep)
    # FastAPI stores the HTTP-facing name on ``field_info.alias`` while ``p.name`` remains
    # the Python parameter name — so filtering by alias is what proves the public API.
    bypass_params = [p for p in dependant.query_params if p.field_info.alias == 'show_deleted']
    assert len(bypass_params) == 1
    assert bypass_params[0].name == 'bypass_default_filters'
    # When no bypass param is configured, no such public alias exists.
    plain_dep = _build_base_dep()
    plain_dependant = get_dependant(path='/', call=plain_dep)
    assert not any(p.field_info.alias == 'show_deleted' for p in plain_dependant.query_params)


def test_max_limit_caps_limit_query() -> None:
    dep = make_list_params_dependency(
        model=Box,
        filters_schema=BoxFilters,
        order_schema=BoxOrdering,
        max_limit=100,
    )
    expected_max = 100
    le_constraints = _get_limit_le(dep)
    assert len(le_constraints) == 1
    assert le_constraints[0].le == expected_max


def test_max_limit_none_removes_cap() -> None:
    dep = make_list_params_dependency(
        model=Box,
        filters_schema=BoxFilters,
        order_schema=BoxOrdering,
        max_limit=None,
    )
    assert _get_limit_le(dep) == []


def test_default_max_limit_is_200() -> None:
    dep = _build_base_dep()
    expected_default_max = 200
    le_constraints = _get_limit_le(dep)
    assert len(le_constraints) == 1
    assert le_constraints[0].le == expected_default_max
