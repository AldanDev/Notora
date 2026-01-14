from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy import Select

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.types import (
    DEFAULT_LIMIT,
    DefaultLimit,
    FilterSpec,
    OptionSpec,
    OrderSpec,
)


@dataclass(slots=True)
class QueryParams[ModelType: GenericBaseModel]:
    filters: Iterable[FilterSpec[ModelType]] | None = None
    ordering: Iterable[OrderSpec[ModelType]] | None = None
    options: Iterable[OptionSpec[ModelType]] | None = None
    limit: int | DefaultLimit | None = DEFAULT_LIMIT
    offset: int = 0
    base_query: Select[tuple[ModelType]] | None = None


@dataclass(slots=True)
class PaginationParams[ModelType: GenericBaseModel]:
    filters: Iterable[FilterSpec[ModelType]] | None = None
    ordering: Iterable[OrderSpec[ModelType]] | None = None
    options: Iterable[OptionSpec[ModelType]] | None = None
    limit: int = 20
    offset: int = 0
    base_query: Select[tuple[ModelType]] | None = None
