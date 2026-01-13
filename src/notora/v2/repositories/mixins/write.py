from collections.abc import Iterable, Sequence
from typing import Any

from sqlalchemy import and_, delete, func, insert, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.dml import ReturningInsert
from sqlalchemy.sql.selectable import TypedReturnsRows

from notora.persistence.models.base import GenericBaseModel
from notora.utils.validation import validate_exclusive_presence

from ..types import FilterSpec, OptionSpec
from .query import FilterableMixin, LoadOptionsMixin, PrimaryKeyMixin


class CreatableMixin[ModelType: GenericBaseModel](LoadOptionsMixin[ModelType]):
    def create(
        self,
        payload: dict[str, Any],
        *,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> ReturningInsert[tuple[ModelType]]:
        stmt = insert(self.model).values(**payload).returning(self.model)
        return self.apply_options(stmt, options)

    def bulk_create(
        self,
        payload: Sequence[dict[str, Any]],
        *,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> ReturningInsert[tuple[ModelType]]:
        stmt = insert(self.model).values(list(payload)).returning(self.model)
        return self.apply_options(stmt, options)


class UpsertableMixin[PKType, ModelType: GenericBaseModel](
    PrimaryKeyMixin[PKType, ModelType],
    LoadOptionsMixin[ModelType],
    FilterableMixin[ModelType],
):
    def upsert(
        self,
        payload: dict[str, Any],
        *,
        conflict_columns: Sequence[InstrumentedAttribute[Any]] | None = None,
        conflict_where: Iterable[FilterSpec[ModelType]] | None = None,
        update_only: Sequence[str] | None = None,
        update_exclude: Sequence[str] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> ReturningInsert[tuple[ModelType]]:
        validate_exclusive_presence(update_only, update_exclude)
        stmt = pg_insert(self.model).values(**payload)

        update_payload = payload
        if update_only is not None:
            update_payload = {k: v for k, v in payload.items() if k in update_only}
        elif update_exclude is not None:
            update_payload = {k: v for k, v in payload.items() if k not in update_exclude}

        clauses = self.merge_filters(conflict_where)
        where_clause = and_(*clauses) if clauses else None

        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_columns or (self.pk_column,),
            index_where=where_clause,
            set_=update_payload,
        ).returning(self.model)
        return self.apply_options(stmt, options)


class UpsertOrSkipMixin[ModelType: GenericBaseModel](
    LoadOptionsMixin[ModelType],
    FilterableMixin[ModelType],
):
    def create_or_skip(
        self,
        payload: dict[str, Any],
        *,
        conflict_columns: Sequence[InstrumentedAttribute[Any]],
        conflict_where: Iterable[FilterSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> ReturningInsert[tuple[ModelType]]:
        stmt = pg_insert(self.model).values(**payload)
        clauses = self.merge_filters(conflict_where)
        where_clause = and_(*clauses) if clauses else None
        stmt = stmt.on_conflict_do_nothing(
            index_elements=conflict_columns,
            index_where=where_clause,
        ).returning(self.model)
        return self.apply_options(stmt, options)


class UpdateMixin[PKType, ModelType: GenericBaseModel](
    PrimaryKeyMixin[PKType, ModelType],
    LoadOptionsMixin[ModelType],
    FilterableMixin[ModelType],
):
    def update_by(
        self,
        payload: dict[str, Any],
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> TypedReturnsRows[tuple[ModelType]]:
        stmt = update(self.model).values(**payload)
        stmt = self.apply_filters(stmt, filters)
        stmt = stmt.returning(self.model)
        return self.apply_options(stmt, options)

    def update(
        self,
        pk: PKType,
        payload: dict[str, Any],
        *,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> TypedReturnsRows[tuple[ModelType]]:
        filters = (lambda _: self.pk_column == pk,)
        return self.update_by(payload, filters=filters, options=options)


class DeleteMixin[PKType, ModelType: GenericBaseModel](
    PrimaryKeyMixin[PKType, ModelType],
    LoadOptionsMixin[ModelType],
    FilterableMixin[ModelType],
):
    def delete_by(
        self,
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> TypedReturnsRows[tuple[ModelType]]:
        stmt = delete(self.model)
        stmt = self.apply_filters(stmt, filters)
        stmt = stmt.returning(self.model)
        return self.apply_options(stmt, options)

    def delete(
        self,
        pk: PKType,
        *,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> TypedReturnsRows[tuple[ModelType]]:
        filters = (lambda _: self.pk_column == pk,)
        return self.delete_by(filters=filters, options=options)


class SoftDeleteMixin[PKType, ModelType: GenericBaseModel](UpdateMixin[PKType, ModelType]):
    deleted_attribute: str = 'deleted_at'

    def soft_delete_by(
        self,
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> TypedReturnsRows[tuple[ModelType]]:
        payload = {self.deleted_attribute: func.now()}
        return super().update_by(payload, filters=filters, options=options)

    def soft_delete(
        self,
        pk: PKType,
        *,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> TypedReturnsRows[tuple[ModelType]]:
        filters = (lambda _: self.pk_column == pk,)
        return self.soft_delete_by(filters=filters, options=options)
