from dataclasses import dataclass
from typing import Any, ClassVar, Literal

from pydantic import BaseModel, ConfigDict
from sqlalchemy.sql import ColumnElement

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.query_dsl import (
    FilterOperator,
    FilterPredicate,
    FilterResolver,
    SortResolver,
    apply_filter_operator,
    resolve_to_column,
)
from notora.v2.repositories.types import FilterSpec, OrderSpec

__all__ = [
    'Filter',
    'PydanticFilterField',
    'PydanticFiltersSchema',
    'PydanticOrderBySchema',
    'PydanticSortField',
]


@dataclass(frozen=True, slots=True)
class PydanticFilterField[ModelType: GenericBaseModel]:
    resolver: FilterResolver[ModelType] | None = None
    predicate: FilterPredicate[ModelType] | None = None
    operator: FilterOperator = 'eq'


@dataclass(frozen=True, slots=True)
class Filter:
    """Annotated-metadata allowlist entry for `PydanticFiltersSchema` fields.

    Use inside `Annotated[T, Filter(...)]`. Holds the same shape as
    `PydanticFilterField` (`resolver` / `predicate` / `operator`); see the
    Filter validation in `__post_init__`.
    """

    resolver: FilterResolver[Any] | None = None
    predicate: FilterPredicate[Any] | None = None
    operator: FilterOperator = 'eq'


@dataclass(frozen=True, slots=True)
class PydanticSortField[ModelType: GenericBaseModel]:
    resolver: SortResolver[ModelType]


class PydanticFiltersSchema[ModelType: GenericBaseModel](BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid')

    filter_fields: ClassVar[dict[str, PydanticFilterField[Any]]] = {}

    def build_filter_specs(self, model: type[ModelType]) -> list[FilterSpec[ModelType]]:
        data = self.model_dump(exclude_unset=True, exclude_none=True)
        specs: list[FilterSpec[ModelType]] = []
        for field_name, value in data.items():
            spec_def = self.filter_fields.get(field_name)
            if spec_def is None:
                continue
            specs.append(_build_one_filter_spec(spec_def, model, value, field_name))
        return specs


class PydanticOrderBySchema[ModelType: GenericBaseModel](BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid')

    sort_fields: ClassVar[dict[str, PydanticSortField[Any]]] = {}

    order_by: str | None = None
    direction: Literal['asc', 'desc'] = 'asc'

    def build_ordering(self, model: type[ModelType]) -> list[OrderSpec[ModelType]]:
        if self.order_by is None:
            return []
        spec_def = self.sort_fields.get(self.order_by)
        if spec_def is None:
            msg = f'Unsupported sort field "{self.order_by}".'
            raise ValueError(msg)
        column = resolve_to_column(spec_def.resolver, model)
        return [column.desc() if self.direction == 'desc' else column.asc()]


def _build_one_filter_spec[ModelType: GenericBaseModel](
    spec_def: PydanticFilterField[ModelType],
    model: type[ModelType],
    value: Any,
    field_name: str,
) -> ColumnElement[bool]:
    if spec_def.predicate is not None:
        return spec_def.predicate(model, spec_def.operator, value)
    if spec_def.resolver is None:
        msg = f'Filter field "{field_name}" requires resolver or predicate.'
        raise ValueError(msg)
    column = resolve_to_column(spec_def.resolver, model)
    return apply_filter_operator(column, spec_def.operator, value)
