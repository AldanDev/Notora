from collections.abc import Iterable, Sequence
from typing import Any, Protocol, cast

from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.selectable import TypedReturnsRows

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.config import RepoConfig
from notora.v2.repositories.mixins import (
    CountableMixin,
    CreateMixin,
    CreateOrSkipMixin,
    DeleteMixin,
    RetrievableMixin,
    SoftDeleteMixin,
    UpdateMixin,
    UpsertMixin,
)
from notora.v2.repositories.params import QueryParams
from notora.v2.repositories.types import DefaultLimit, FilterSpec, OptionSpec, OrderSpec


class Repository[PKType, ModelType: GenericBaseModel](
    RetrievableMixin[PKType, ModelType],
    CreateMixin[ModelType],
    UpsertMixin[PKType, ModelType],
    CreateOrSkipMixin[ModelType],
    UpdateMixin[PKType, ModelType],
    DeleteMixin[PKType, ModelType],
    CountableMixin[ModelType],
):
    """Composition-friendly base repository built out of mixins."""

    def __init__(  # noqa: C901
        self, model: type[ModelType], *, config: RepoConfig[ModelType] | None = None
    ) -> None:
        self.model = model
        if config is None:
            return
        if config.default_limit is not None:
            self.default_limit = config.default_limit
        if config.default_options is not None:
            self.default_options = config.default_options
        if config.default_filters is not None:
            self.default_filters = config.default_filters
        if config.default_ordering is not None:
            self.default_ordering = config.default_ordering
        if config.fallback_sort_attribute is not None:
            self.fallback_sort_attribute = config.fallback_sort_attribute
        if config.pk_attribute is not None:
            self.pk_attribute = config.pk_attribute


class SoftDeleteRepository[PKType, ModelType: GenericBaseModel](
    RetrievableMixin[PKType, ModelType],
    CreateMixin[ModelType],
    UpsertMixin[PKType, ModelType],
    CreateOrSkipMixin[ModelType],
    SoftDeleteMixin[PKType, ModelType],
    DeleteMixin[PKType, ModelType],
    CountableMixin[ModelType],
):
    """Repository variant with soft-delete helpers."""

    apply_soft_delete_filter: bool = True

    def _soft_delete_filter(self) -> FilterSpec[ModelType]:
        column = cast(InstrumentedAttribute[Any], getattr(self.model, self.deleted_attribute))
        return column.is_(None)

    def __init__(  # noqa: C901
        self, model: type[ModelType], *, config: RepoConfig[ModelType] | None = None
    ) -> None:
        self.model = model
        apply_soft_delete_filter = self.apply_soft_delete_filter
        if config is not None:
            if config.default_limit is not None:
                self.default_limit = config.default_limit
            if config.default_options is not None:
                self.default_options = config.default_options
            if config.default_filters is not None:
                self.default_filters = config.default_filters
            if config.default_ordering is not None:
                self.default_ordering = config.default_ordering
            if config.fallback_sort_attribute is not None:
                self.fallback_sort_attribute = config.fallback_sort_attribute
            if config.pk_attribute is not None:
                self.pk_attribute = config.pk_attribute
            if config.apply_soft_delete_filter is not None:
                apply_soft_delete_filter = config.apply_soft_delete_filter
        if apply_soft_delete_filter:
            base_filters = tuple(self.default_filters)
            self.default_filters = (*base_filters, self._soft_delete_filter())


class RepositoryProtocol[PKType, ModelType: GenericBaseModel](Protocol):
    model: type[ModelType]
    pk_attribute: str
    default_limit: int

    def list(
        self,
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
        limit: int | DefaultLimit | None = ...,
        offset: int = 0,
        ordering: Iterable[OrderSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        base_query: Any | None = None,
    ) -> TypedReturnsRows[tuple[ModelType]]: ...

    def list_by_params(
        self, params: QueryParams[ModelType]
    ) -> TypedReturnsRows[tuple[ModelType]]: ...

    def count(
        self,
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
    ) -> TypedReturnsRows[tuple[int]]: ...

    def retrieve(
        self,
        pk: PKType,
        *,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> TypedReturnsRows[tuple[ModelType]]: ...

    def retrieve_by(
        self,
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
        ordering: Iterable[OrderSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> TypedReturnsRows[tuple[ModelType]]: ...

    def retrieve_one_by(
        self,
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
        ordering: Iterable[OrderSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> TypedReturnsRows[tuple[ModelType]]: ...

    def create(
        self,
        payload: dict[str, Any],
        *,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> TypedReturnsRows[tuple[ModelType]]: ...

    def create_or_skip(
        self,
        payload: dict[str, Any],
        *,
        conflict_columns: Sequence[InstrumentedAttribute[Any]],
        conflict_where: Iterable[FilterSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> TypedReturnsRows[tuple[ModelType]]: ...

    def upsert(
        self,
        payload: dict[str, Any],
        *,
        conflict_columns: Sequence[InstrumentedAttribute[Any]] | None = None,
        conflict_where: Iterable[FilterSpec[ModelType]] | None = None,
        update_only: Sequence[str] | None = None,
        update_exclude: Sequence[str] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> TypedReturnsRows[tuple[ModelType]]: ...

    def update(
        self,
        pk: PKType,
        payload: dict[str, Any],
        *,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> TypedReturnsRows[tuple[ModelType]]: ...

    def update_by(
        self,
        payload: dict[str, Any],
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> TypedReturnsRows[tuple[ModelType]]: ...

    def delete(
        self,
        pk: PKType,
        *,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> TypedReturnsRows[tuple[ModelType]]: ...

    def delete_by(
        self,
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> TypedReturnsRows[tuple[ModelType]]: ...


class SoftDeleteRepositoryProtocol[PKType, ModelType: GenericBaseModel](
    RepositoryProtocol[PKType, ModelType],
    Protocol,
):
    def soft_delete(
        self,
        pk: PKType,
        *,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> TypedReturnsRows[tuple[ModelType]]: ...

    def soft_delete_by(
        self,
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> TypedReturnsRows[tuple[ModelType]]: ...
