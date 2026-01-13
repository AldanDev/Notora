from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, Self

from sqlalchemy.sql import ColumnElement
from sqlalchemy.sql.base import ExecutableOption
from sqlalchemy.sql.expression import UnaryExpression

from notora.persistence.models.base import GenericBaseModel

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
