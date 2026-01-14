import operator
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Literal, cast

from pydantic import BaseModel, Field, TypeAdapter, field_validator
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql import ColumnElement

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.params import QueryParams
from notora.v2.repositories.types import DEFAULT_LIMIT, DefaultLimit, OrderClause

type FilterOperator = Literal['eq', 'ne', 'lt', 'lte', 'gt', 'gte', 'in', 'ilike', 'isnull']
type SortDirection = Literal['asc', 'desc']
type FilterResolver[ModelType: GenericBaseModel] = (
    InstrumentedAttribute[Any]
    | ColumnElement[Any]
    | Callable[[type[ModelType]], InstrumentedAttribute[Any] | ColumnElement[Any]]
)
type SortResolver[ModelType: GenericBaseModel] = (
    InstrumentedAttribute[Any]
    | ColumnElement[Any]
    | Callable[[type[ModelType]], InstrumentedAttribute[Any] | ColumnElement[Any]]
)
type FilterPredicate[ModelType: GenericBaseModel] = Callable[
    [type[ModelType], FilterOperator, Any], ColumnElement[bool]
]

DEFAULT_OPERATORS: frozenset[FilterOperator] = frozenset({
    'eq',
    'ne',
    'lt',
    'lte',
    'gt',
    'gte',
    'in',
    'ilike',
    'isnull',
})
FILTER_PARTS_MIN = 2
FILTER_PARTS_WITH_VALUE = 3


class QueryInput(BaseModel):
    filter: list[str] = Field(default_factory=list)
    sort: list[str] = Field(default_factory=list)
    limit: int | None = None
    offset: int = 0

    @field_validator('limit')
    @classmethod
    def _validate_limit(cls, value: int | None) -> int | None:
        if value is None:
            return value
        if value <= 0:
            msg = 'limit must be a positive integer.'
            raise ValueError(msg)
        return value

    @field_validator('offset')
    @classmethod
    def _validate_offset(cls, value: int) -> int:
        if value < 0:
            msg = 'offset must be zero or a positive integer.'
            raise ValueError(msg)
        return value


@dataclass(frozen=True, slots=True)
class FilterToken:
    field: str
    operator: FilterOperator
    raw_value: str | None


@dataclass(frozen=True, slots=True)
class SortToken:
    field: str
    direction: SortDirection


@dataclass(frozen=True, slots=True)
class FilterField[ModelType: GenericBaseModel]:
    resolver: FilterResolver[ModelType] | None = None
    predicate: FilterPredicate[ModelType] | None = None
    operators: frozenset[FilterOperator] = DEFAULT_OPERATORS
    value_type: type[Any] | TypeAdapter[Any] | None = None


@dataclass(frozen=True, slots=True)
class SortField[ModelType: GenericBaseModel]:
    resolver: SortResolver[ModelType]


def parse_filter_token(raw: str) -> FilterToken:
    parts = raw.split(':', 2)
    if len(parts) < FILTER_PARTS_MIN:
        msg = 'filter must be in "field:op:value" format.'
        raise ValueError(msg)
    field_name = parts[0].strip()
    op = parts[1].strip()
    raw_value = parts[2] if len(parts) == FILTER_PARTS_WITH_VALUE else None
    if not field_name:
        msg = 'filter field name cannot be empty.'
        raise ValueError(msg)
    if op not in DEFAULT_OPERATORS:
        msg = f'Unsupported filter operator "{op}".'
        raise ValueError(msg)
    operator = cast(FilterOperator, op)
    if raw_value is not None:
        raw_value = raw_value.strip()
        if not raw_value:
            raw_value = None
    return FilterToken(field=field_name, operator=operator, raw_value=raw_value)


def parse_sort_token(raw: str) -> SortToken:
    value = raw.strip()
    if not value:
        msg = 'sort field name cannot be empty.'
        raise ValueError(msg)
    direction: SortDirection
    if value[0] == '-':
        direction = 'desc'
        field_name = value[1:]
    elif value[0] == '+':
        direction = 'asc'
        field_name = value[1:]
    else:
        direction = 'asc'
        field_name = value
    field_name = field_name.strip()
    if not field_name:
        msg = 'sort field name cannot be empty.'
        raise ValueError(msg)
    return SortToken(field=field_name, direction=direction)


def _resolve_resolver[ModelType: GenericBaseModel](
    resolver: FilterResolver[ModelType] | SortResolver[ModelType],
    model: type[ModelType],
) -> InstrumentedAttribute[Any] | ColumnElement[Any]:
    return resolver(model) if callable(resolver) else resolver


def _parse_scalar_value(field: FilterField[Any], raw_value: str) -> Any:
    if field.value_type is None:
        return raw_value
    adapter = (
        field.value_type
        if isinstance(field.value_type, TypeAdapter)
        else TypeAdapter(field.value_type)
    )
    return adapter.validate_python(raw_value)


def _parse_filter_value(token: FilterToken, field: FilterField[Any]) -> Any:
    if token.operator == 'isnull':
        if token.raw_value is None:
            return True
        return TypeAdapter(bool).validate_python(token.raw_value)
    if token.raw_value is None:
        msg = f'Filter "{token.field}:{token.operator}" requires a value.'
        raise ValueError(msg)
    if token.operator == 'in':
        items = [item for item in token.raw_value.split(',') if item]
        if not items:
            msg = f'Filter "{token.field}:{token.operator}" requires a value.'
            raise ValueError(msg)
        return [_parse_scalar_value(field, item) for item in items]
    return _parse_scalar_value(field, token.raw_value)


def _apply_operator(
    column: ColumnElement[Any] | InstrumentedAttribute[Any],
    op: FilterOperator,
    value: Any,
) -> ColumnElement[bool]:
    operators: dict[
        FilterOperator,
        Callable[[ColumnElement[Any] | InstrumentedAttribute[Any], Any], ColumnElement[bool]],
    ] = {
        'eq': operator.eq,
        'ne': operator.ne,
        'lt': operator.lt,
        'lte': operator.le,
        'gt': operator.gt,
        'gte': operator.ge,
        'in': lambda col, val: col.in_(val),
        'ilike': lambda col, val: col.ilike(val),
        'isnull': lambda col, val: col.is_(None) if val else col.is_not(None),
    }
    handler = operators.get(op)
    if handler is None:
        msg = f'Unsupported filter operator "{op}".'
        raise ValueError(msg)
    return handler(column, value)


def build_filter_clauses[ModelType: GenericBaseModel](
    tokens: Iterable[FilterToken],
    *,
    model: type[ModelType],
    fields: Mapping[str, FilterField[ModelType]],
) -> list[ColumnElement[bool]]:
    clauses: list[ColumnElement[bool]] = []
    for token in tokens:
        field = fields.get(token.field)
        if field is None:
            msg = f'Unsupported filter field "{token.field}".'
            raise ValueError(msg)
        if token.operator not in field.operators:
            msg = f'Operator "{token.operator}" is not allowed for "{token.field}".'
            raise ValueError(msg)
        value = _parse_filter_value(token, field)
        if field.predicate is not None:
            clause = field.predicate(model, token.operator, value)
        elif field.resolver is not None:
            column = _resolve_resolver(field.resolver, model)
            clause = _apply_operator(column, token.operator, value)
        else:
            msg = f'Filter field "{token.field}" requires resolver or predicate.'
            raise ValueError(msg)
        clauses.append(clause)
    return clauses


def build_sort_clauses[ModelType: GenericBaseModel](
    tokens: Iterable[SortToken],
    *,
    model: type[ModelType],
    fields: Mapping[str, SortField[ModelType]],
) -> list[OrderClause]:
    clauses: list[OrderClause] = []
    for token in tokens:
        field = fields.get(token.field)
        if field is None:
            msg = f'Unsupported sort field "{token.field}".'
            raise ValueError(msg)
        column = _resolve_resolver(field.resolver, model)
        if token.direction == 'desc':
            clauses.append(column.desc())
        else:
            clauses.append(column.asc())
    return clauses


def build_query_params[ModelType: GenericBaseModel](
    query: QueryInput,
    *,
    model: type[ModelType],
    filter_fields: Mapping[str, FilterField[ModelType]] | None = None,
    sort_fields: Mapping[str, SortField[ModelType]] | None = None,
    base_query: Any | None = None,
) -> QueryParams[ModelType]:
    filter_fields = filter_fields or {}
    sort_fields = sort_fields or {}
    if query.filter and not filter_fields:
        msg = 'Filter fields mapping is required when filters are provided.'
        raise ValueError(msg)
    if query.sort and not sort_fields:
        msg = 'Sort fields mapping is required when sorting is provided.'
        raise ValueError(msg)
    filter_tokens = [parse_filter_token(raw) for raw in query.filter]
    sort_tokens = [parse_sort_token(raw) for raw in query.sort]
    filters = (
        build_filter_clauses(filter_tokens, model=model, fields=filter_fields)
        if filter_tokens
        else None
    )
    ordering = (
        build_sort_clauses(sort_tokens, model=model, fields=sort_fields) if sort_tokens else None
    )
    limit: int | DefaultLimit | None = DEFAULT_LIMIT if query.limit is None else query.limit
    return QueryParams(
        filters=filters,
        ordering=ordering,
        limit=limit,
        offset=query.offset,
        base_query=base_query,
    )


def make_query_params_dependency[ModelType: GenericBaseModel](
    *,
    model: type[ModelType],
    filter_fields: Mapping[str, FilterField[ModelType]] | None = None,
    sort_fields: Mapping[str, SortField[ModelType]] | None = None,
    base_query: Any | None = None,
) -> Callable[..., QueryParams[ModelType]]:
    try:
        fastapi = __import__('fastapi')
    except Exception as exc:  # pragma: no cover - only used in FastAPI apps
        msg = 'fastapi is required to use make_query_params_dependency.'
        raise RuntimeError(msg) from exc

    depends = fastapi.Depends()

    def _dependency(query: QueryInput = depends) -> QueryParams[ModelType]:
        return build_query_params(
            query,
            model=model,
            filter_fields=filter_fields,
            sort_fields=sort_fields,
            base_query=base_query,
        )

    return _dependency
