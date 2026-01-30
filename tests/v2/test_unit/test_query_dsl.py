import pytest
from pydantic import ValidationError
from sqlalchemy import Integer, String
from sqlalchemy.orm import InstrumentedAttribute, Mapped, mapped_column

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories import FilterField, QueryInput, SortField, build_query_params
from notora.v2.repositories.types import DEFAULT_LIMIT


class WidgetQuery(GenericBaseModel):
    name: Mapped[str] = mapped_column(String)
    count: Mapped[int] = mapped_column(Integer)


EXPECTED_LIMIT = 10
EXPECTED_OFFSET = 5
EXPECTED_FILTERS = 2
EXPECTED_ORDERING = 1


def _name_column(model: type[WidgetQuery]) -> InstrumentedAttribute[str]:
    return model.name


def _count_column(model: type[WidgetQuery]) -> InstrumentedAttribute[int]:
    return model.count


def test_build_query_params_builds_filters_and_sort() -> None:
    query = QueryInput(
        filter=['name:eq:alpha', 'count:gte:2'],
        sort=['-name'],
        limit=EXPECTED_LIMIT,
        offset=EXPECTED_OFFSET,
    )
    filter_fields: dict[str, FilterField[WidgetQuery]] = {
        'name': FilterField(resolver=_name_column, value_type=str),
        'count': FilterField(resolver=_count_column, value_type=int),
    }
    sort_fields: dict[str, SortField[WidgetQuery]] = {'name': SortField(resolver=_name_column)}

    params = build_query_params(
        query,
        model=WidgetQuery,
        filter_fields=filter_fields,
        sort_fields=sort_fields,
    )

    assert params.limit == EXPECTED_LIMIT
    assert params.offset == EXPECTED_OFFSET
    assert params.filters is not None
    assert params.ordering is not None
    assert len(list(params.filters)) == EXPECTED_FILTERS
    assert len(list(params.ordering)) == EXPECTED_ORDERING


def test_build_query_params_rejects_unknown_filter_field() -> None:
    query = QueryInput(filter=['unknown:eq:1'])
    filter_fields: dict[str, FilterField[WidgetQuery]] = {
        'name': FilterField(resolver=_name_column, value_type=str),
    }

    with pytest.raises(ValueError, match='Unsupported filter field'):
        build_query_params(query, model=WidgetQuery, filter_fields=filter_fields)


def test_build_query_params_accepts_direct_attributes() -> None:
    query = QueryInput(filter=['name:eq:alpha'], sort=['+count'])
    filter_fields: dict[str, FilterField[WidgetQuery]] = {
        'name': FilterField(resolver=WidgetQuery.name, value_type=str),
    }
    sort_fields: dict[str, SortField[WidgetQuery]] = {
        'count': SortField(resolver=WidgetQuery.count),
    }

    params = build_query_params(
        query,
        model=WidgetQuery,
        filter_fields=filter_fields,
        sort_fields=sort_fields,
    )

    assert params.limit is DEFAULT_LIMIT
    assert params.filters is not None
    assert params.ordering is not None


def test_build_query_params_parses_in_and_isnull() -> None:
    query = QueryInput(filter=['count:in:1,2', 'name:isnull'])
    filter_fields: dict[str, FilterField[WidgetQuery]] = {
        'name': FilterField(resolver=_name_column, value_type=str),
        'count': FilterField(resolver=_count_column, value_type=int),
    }

    params = build_query_params(query, model=WidgetQuery, filter_fields=filter_fields)
    clauses = list(params.filters or ())

    assert ' IN ' in str(clauses[0])
    assert ' IS NULL' in str(clauses[1])


def test_build_query_params_rejects_disallowed_operator() -> None:
    query = QueryInput(filter=['name:ilike:alpha'])
    filter_fields: dict[str, FilterField[WidgetQuery]] = {
        'name': FilterField(resolver=_name_column, operators=frozenset({'eq'})),
    }

    with pytest.raises(ValueError, match='Operator'):
        build_query_params(query, model=WidgetQuery, filter_fields=filter_fields)


def test_query_input_rejects_non_positive_limit() -> None:
    with pytest.raises(ValidationError, match='limit must be a positive integer'):
        QueryInput(limit=0)
