from collections.abc import Callable
from typing import Any, Protocol, Self

from sqlalchemy.sql import ColumnElement
from sqlalchemy.sql.base import ExecutableOption
from sqlalchemy.sql.expression import UnaryExpression

from notora.v2.models.base import GenericBaseModel


class _DefaultLimit:
    def __repr__(self) -> str:
        return 'DEFAULT_LIMIT'


DEFAULT_LIMIT = _DefaultLimit()
type DefaultLimit = _DefaultLimit

type FilterClause = ColumnElement[bool]
type FilterFactory[ModelType: GenericBaseModel] = Callable[[type[ModelType]], FilterClause]
type FilterSpec[ModelType: GenericBaseModel] = FilterClause | FilterFactory[ModelType]

type OrderClause = ColumnElement[Any] | UnaryExpression[Any]
type OrderFactory[ModelType: GenericBaseModel] = Callable[[type[ModelType]], OrderClause]
type OrderSpec[ModelType: GenericBaseModel] = OrderClause | OrderFactory[ModelType]

type OptionFactory[ModelType: GenericBaseModel] = Callable[[type[ModelType]], ExecutableOption]
type OptionSpec[ModelType: GenericBaseModel] = ExecutableOption | OptionFactory[ModelType]


class SupportsWhere(Protocol):
    """Subset of SQLAlchemy statements that expose ``where``."""

    def where(self, *criteria: Any) -> Self: ...


class SupportsOptions(Protocol):
    """SQLAlchemy statements that accept loader options."""

    def options(self, *options: ExecutableOption) -> Self: ...
