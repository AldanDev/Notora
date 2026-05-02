from collections.abc import Mapping
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

    Intentionally not generic over a `ModelType`. The schema's `ModelType`
    parameter (`PydanticFiltersSchema[Thing]`) is the source of truth — adding
    `Filter[ModelType]` would force every `Annotated[...]` site to repeat the
    type argument with little payoff. As a result, `resolver` and `predicate`
    are typed against an unbound `Any`-model: a mismatch such as
    `Filter(resolver=OtherModel.x)` inside `PydanticFiltersSchema[Thing]` is
    not caught by the type checker and surfaces only at runtime in
    `build_filter_specs(model)`.
    """

    resolver: FilterResolver[Any] | None = None
    predicate: FilterPredicate[Any] | None = None
    operator: FilterOperator = 'eq'

    def __post_init__(self) -> None:
        if (self.resolver is None) == (self.predicate is None):
            msg = (
                'Filter requires exactly one of resolver= or predicate= '
                '(got both or neither).'
            )
            raise TypeError(msg)


@dataclass(frozen=True, slots=True)
class PydanticSortField[ModelType: GenericBaseModel]:
    resolver: SortResolver[ModelType]


def _extract_annotated_filters(cls: type[BaseModel]) -> dict[str, Filter]:
    """Read Filter(...) instances out of each field's `Annotated[...]` metadata.

    Pydantic v2 stores third-party Annotated metadata in `model_fields[name].metadata`.
    Filter is third-party (not a `FieldInfo`), so it lives there untouched.
    """
    out: dict[str, Filter] = {}
    for name, field_info in cls.model_fields.items():
        filters = [m for m in field_info.metadata if isinstance(m, Filter)]
        if not filters:
            continue
        if len(filters) > 1:
            msg = (
                f'{cls.__name__}.{name}: multiple Filter(...) entries in '
                f'Annotated[...] — only one is allowed per field.'
            )
            raise TypeError(msg)
        out[name] = filters[0]
    return out


class PydanticFiltersSchema[ModelType: GenericBaseModel](BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='forbid')

    filter_fields: ClassVar[dict[str, PydanticFilterField[Any]]] = {}
    _annotated_filter_fields: ClassVar[dict[str, Filter]] = {}

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        super().__pydantic_init_subclass__(**kwargs)
        annotated = _extract_annotated_filters(cls)
        legacy = cls.filter_fields  # resolves through MRO; sees inherited values

        if legacy and annotated:
            colliding = sorted(set(legacy) & set(annotated))
            if colliding:
                detail = f'Overlapping fields: {", ".join(colliding)}.'
            else:
                detail = (
                    f'Annotated fields: {sorted(annotated)}; '
                    f'filter_fields keys: {sorted(legacy)}.'
                )
            msg = (
                f'{cls.__name__} mixes legacy `filter_fields` ClassVar and '
                f'`Annotated[..., Filter(...)]` declarations — pick one style '
                f'per schema. {detail}'
            )
            raise TypeError(msg)

        cls._annotated_filter_fields = annotated

    def build_filter_specs(self, model: type[ModelType]) -> list[FilterSpec[ModelType]]:
        data = self.model_dump(exclude_unset=True, exclude_none=True)
        # Mapping is read-only / covariant; either dict literal type satisfies it.
        sources: Mapping[str, PydanticFilterField[Any] | Filter] = (
            self.filter_fields or self._annotated_filter_fields
        )
        specs: list[FilterSpec[ModelType]] = []
        for field_name, value in data.items():
            spec_def = sources.get(field_name)
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
    spec_def: PydanticFilterField[ModelType] | Filter,
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
