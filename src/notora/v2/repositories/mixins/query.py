from collections.abc import Iterable, Sequence
from typing import Any, cast

from sqlalchemy import Select, func, select
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.base import ExecutableOption

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.params import QueryParams
from notora.v2.repositories.types import (
    DEFAULT_LIMIT,
    DefaultLimit,
    FilterClause,
    FilterSpec,
    OptionSpec,
    OrderClause,
    OrderSpec,
    SupportsOptions,
    SupportsWhere,
)


class LoadOptionsMixin[ModelType: GenericBaseModel]:
    """Adds ``.options`` support with overridable defaults."""

    model: type[ModelType]
    default_options: Sequence[OptionSpec[ModelType]] = ()

    def _resolve_option(self, spec: OptionSpec[ModelType]) -> ExecutableOption:
        return spec(self.model) if callable(spec) else spec

    def merge_options(
        self,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> tuple[ExecutableOption, ...]:
        custom = tuple(options or ())
        specs = (*self.default_options, *custom)
        return tuple(self._resolve_option(spec) for spec in specs)

    def apply_options[StatementT: SupportsOptions](
        self,
        statement: StatementT,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> StatementT:
        merged = self.merge_options(options)
        if merged:
            statement = statement.options(*merged)
        return statement


class FilterableMixin[ModelType: GenericBaseModel]:
    model: type[ModelType]
    default_filters: Sequence[FilterSpec[ModelType]] = ()

    def _resolve_filter(self, spec: FilterSpec[ModelType]) -> FilterClause:
        return spec(self.model) if callable(spec) else spec

    def merge_filters(
        self,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
    ) -> tuple[FilterClause, ...]:
        custom = tuple(filters or ())
        specs = (*self.default_filters, *custom)
        return tuple(self._resolve_filter(spec) for spec in specs)

    def apply_filters[StatementT: SupportsWhere](
        self,
        statement: StatementT,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
    ) -> StatementT:
        for clause in self.merge_filters(filters):
            statement = statement.where(clause)
        return statement


class OrderableMixin[ModelType: GenericBaseModel]:
    model: type[ModelType]
    default_ordering: Sequence[OrderSpec[ModelType]] = ()
    fallback_sort_attribute: str = 'id'

    def _resolve_order(self, spec: OrderSpec[ModelType]) -> OrderClause:
        return spec(self.model) if callable(spec) else spec

    def merge_ordering(
        self,
        ordering: Iterable[OrderSpec[ModelType]] | None = None,
    ) -> tuple[Any, ...]:
        custom = tuple(ordering or ())
        specs = (*self.default_ordering, *custom)
        resolved = [self._resolve_order(spec) for spec in specs]
        if not resolved and hasattr(self.model, self.fallback_sort_attribute):
            pk_column = getattr(self.model, self.fallback_sort_attribute)
            resolved.append(pk_column.asc())
        return tuple(resolved)

    def apply_ordering(
        self,
        statement: Select[Any],
        ordering: Iterable[OrderSpec[ModelType]] | None = None,
    ) -> Select[Any]:
        clauses = self.merge_ordering(ordering)
        if clauses:
            statement = statement.order_by(*clauses)
        return statement


class SelectableMixin[ModelType: GenericBaseModel](LoadOptionsMixin[ModelType]):
    def select(
        self,
        *,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> Select[tuple[ModelType]]:
        stmt = select(self.model)
        return self.apply_options(stmt, options)


class ListableMixin[ModelType: GenericBaseModel](
    SelectableMixin[ModelType],
    FilterableMixin[ModelType],
    OrderableMixin[ModelType],
):
    default_limit: int = 50

    def list(
        self,
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
        limit: int | DefaultLimit | None = DEFAULT_LIMIT,
        offset: int = 0,
        ordering: Iterable[OrderSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        base_query: Select[tuple[ModelType]] | None = None,
    ) -> Select[tuple[ModelType]]:
        if base_query is None:
            stmt = self.select(options=options)
        else:
            stmt = self.apply_options(base_query, options)
        stmt = self.apply_filters(stmt, filters)
        stmt = self.apply_ordering(stmt, ordering)
        if limit is DEFAULT_LIMIT:
            limit_value = self.default_limit
        elif limit is None:
            limit_value = None
        else:
            limit_value = cast(int | None, limit)
        if limit_value is not None:
            stmt = stmt.limit(limit_value)
        if offset:
            stmt = stmt.offset(offset)
        return stmt

    def list_by_params(self, params: QueryParams[ModelType]) -> Select[tuple[ModelType]]:
        return self.list(
            filters=params.filters,
            limit=params.limit,
            offset=params.offset,
            ordering=params.ordering,
            options=params.options,
            base_query=params.base_query,
        )


class PrimaryKeyMixin[PKType, ModelType: GenericBaseModel]:
    model: type[ModelType]
    pk_attribute: str = 'id'

    @property
    def pk_column(self) -> InstrumentedAttribute[PKType]:
        return cast(InstrumentedAttribute[PKType], getattr(self.model, self.pk_attribute))


class RetrievableMixin[PKType, ModelType: GenericBaseModel](
    PrimaryKeyMixin[PKType, ModelType],
    ListableMixin[ModelType],
):
    def retrieve(
        self,
        pk: PKType,
        *,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> Select[tuple[ModelType]]:
        return self.list(
            filters=(cast(FilterClause, self.pk_column == pk),),
            limit=1,
            options=options,
        )

    def retrieve_by(
        self,
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
        ordering: Iterable[OrderSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> Select[tuple[ModelType]]:
        stmt = self.select(options=options)
        stmt = self.apply_filters(stmt, filters)
        stmt = self.apply_ordering(stmt, ordering)
        return stmt

    def retrieve_one_by(
        self,
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
        ordering: Iterable[OrderSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> Select[tuple[ModelType]]:
        stmt = self.retrieve_by(filters=filters, ordering=ordering, options=options)
        return stmt.limit(1)


class CountableMixin[ModelType: GenericBaseModel](FilterableMixin[ModelType]):
    def count(
        self,
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
    ) -> Select[tuple[int]]:
        stmt = select(func.count()).select_from(self.model)
        return self.apply_filters(stmt, filters)
