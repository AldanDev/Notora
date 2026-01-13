from collections.abc import Iterable, Sequence
from typing import Any, Protocol

from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.selectable import TypedReturnsRows

from notora.v2.models.base import GenericBaseModel

from ...repositories.types import FilterSpec, OptionSpec, OrderSpec


class RepositoryProtocol[PKType, ModelType: GenericBaseModel](Protocol):
    def list(
        self,
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
        limit: int | None = None,
        offset: int = 0,
        ordering: Iterable[OrderSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        base_query: Any | None = None,
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


class RepositoryAccessorMixin[PKType, ModelType: GenericBaseModel]:
    repo: RepositoryProtocol[PKType, ModelType]

    def _extract_pk(self, entity: ModelType) -> PKType:
        pk_attr = getattr(self.repo, 'pk_attribute', 'id')
        return getattr(entity, pk_attr)
