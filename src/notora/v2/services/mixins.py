from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import Any, ClassVar, Literal, Protocol

from pydantic import BaseModel as PydanticModel
from sqlalchemy import Executable, delete, exc, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.selectable import TypedReturnsRows

from notora.exceptions.common import AlreadyExistsError, FKNotFoundError, NotFoundError
from notora.persistence.models.base import GenericBaseModel
from notora.schemas.base import BaseResponseSchema, PaginatedResponseSchema
from notora.utils.pagination import calculate_pagination

from ..repositories.types import FilterSpec, OptionSpec, OrderSpec


class SerializerProtocol[ModelType: GenericBaseModel](Protocol):
    def serialize_one(
        self,
        obj: ModelType,
        *,
        schema: type[BaseResponseSchema] | Literal[False] | None = None,
    ) -> BaseResponseSchema | ModelType: ...

    def serialize_many(
        self,
        objs: Iterable[ModelType],
        *,
        schema: type[BaseResponseSchema] | Literal[False] | None = None,
        prefer_list_schema: bool = True,
    ) -> list[BaseResponseSchema] | list[ModelType]: ...


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


class SerializerMixin[ModelType: GenericBaseModel, ResponseSchema: BaseResponseSchema]:
    detail_schema: type[ResponseSchema] | None = None
    list_schema: type[ResponseSchema] | None = None

    def serialize_one(
        self,
        obj: ModelType,
        *,
        schema: type[BaseResponseSchema] | Literal[False] | None = None,
    ) -> BaseResponseSchema | ModelType:
        match schema:
            case False:
                return obj
            case None:
                schema = self.detail_schema
        if schema is None:
            return obj
        return schema.model_validate(obj)

    def serialize_many(
        self,
        objs: Iterable[ModelType],
        *,
        schema: type[BaseResponseSchema] | Literal[False] | None = None,
        prefer_list_schema: bool = True,
    ) -> list[BaseResponseSchema | ModelType]:
        if schema is None and prefer_list_schema:
            schema = self.list_schema or self.detail_schema
        return [self.serialize_one(obj, schema=schema) for obj in objs]


class SessionExecutorMixin[PKType, ModelType: GenericBaseModel]:
    _unique_violation_errors: ClassVar[dict[str, str]] = {}
    _fk_violation_errors: ClassVar[dict[str, str]] = {}

    _unique_constraint_pattern = re.compile(
        r'.*duplicate key value violates unique constraint "(?P<name>\w+)"',
    )
    _fk_constraint_pattern = re.compile(
        r'.*insert or update on table "(?P<table_name>\w+)" '
        r'violates foreign key constraint "(?P<fk_name>\w+)"',
    )

    @property
    def _not_found_error(self) -> str:
        return f'{self.__class__.__name__.removesuffix("Service")} not found.'

    async def _execute(
        self,
        session: AsyncSession,
        statement: TypedReturnsRows[tuple[ModelType]],
    ):
        try:
            return await session.execute(statement)
        except exc.IntegrityError as err:
            raise self._translate_integrity_error(err) from err

    async def execute_for_one(
        self,
        session: AsyncSession,
        statement: TypedReturnsRows[tuple[ModelType]],
    ) -> ModelType:
        result = await self._execute(session, statement)
        entity = result.unique().scalar_one_or_none()
        if entity is None:
            raise NotFoundError[PKType](self._not_found_error)
        return entity

    async def execute_optional(
        self,
        session: AsyncSession,
        statement: TypedReturnsRows[tuple[ModelType]],
    ) -> ModelType | None:
        result = await self._execute(session, statement)
        return result.unique().scalar_one_or_none()

    def _translate_integrity_error(self, err: exc.IntegrityError) -> Exception:
        if match := self._fk_constraint_pattern.match(err.args[0]):
            fk_name = match.group('fk_name')
            table_name = match.group('table_name')
            return FKNotFoundError(
                self._fk_violation_errors.get(fk_name, 'Related object not found.'),
                fk_name=fk_name,
                table_name=table_name,
            )
        if match := self._unique_constraint_pattern.match(err.args[0]):
            constraint = match.group('name')
            return AlreadyExistsError(
                self._unique_violation_errors.get(constraint, 'Entity already exists.'),
                constraint_name=constraint,
            )
        return err


class PayloadMixin[ModelType: GenericBaseModel]:
    @staticmethod
    def _dump_payload(
        data: PydanticModel | dict[str, Any],
        *,
        exclude_unset: bool,
    ) -> dict[str, Any]:
        if isinstance(data, dict):
            return dict(data)
        return data.model_dump(exclude_unset=exclude_unset)


class RepositoryAccessorMixin[PKType, ModelType: GenericBaseModel]:
    repo: RepositoryProtocol[PKType, ModelType]

    def _extract_pk(self, entity: ModelType) -> PKType:
        pk_attr = getattr(self.repo, 'pk_attribute', 'id')
        return getattr(entity, pk_attr)


class ListingServiceMixin[PKType, ModelType: GenericBaseModel](
    RepositoryAccessorMixin[PKType, ModelType],
    SerializerProtocol[ModelType],
):
    async def list_raw(
        self,
        session: AsyncSession,
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
        limit: int | None = None,
        offset: int = 0,
        ordering: Iterable[OrderSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        base_query: Any | None = None,
    ) -> Sequence[ModelType]:
        query = self.repo.list(
            filters=filters,
            limit=limit,
            offset=offset,
            ordering=ordering,
            options=options,
            base_query=base_query,
        )
        result = await session.scalars(query)
        return result.all()

    async def list(
        self,
        session: AsyncSession,
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
        limit: int | None = None,
        offset: int = 0,
        ordering: Iterable[OrderSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        base_query: Any | None = None,
        schema: type[BaseResponseSchema] | Literal[False] | None = None,
    ) -> list[BaseResponseSchema] | list[ModelType]:
        rows = await self.list_raw(
            session,
            filters=filters,
            limit=limit,
            offset=offset,
            ordering=ordering,
            options=options,
            base_query=base_query,
        )
        return self.serialize_many(rows, schema=schema)


class PaginationServiceMixin[PKType, ModelType: GenericBaseModel](
    ListingServiceMixin[PKType, ModelType],
):
    async def paginate(
        self,
        session: AsyncSession,
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
        limit: int = 20,
        offset: int = 0,
        ordering: Iterable[OrderSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        schema: type[BaseResponseSchema] | Literal[False] | None = None,
    ) -> PaginatedResponseSchema[BaseResponseSchema | ModelType]:
        data = await self.list_raw(
            session,
            filters=filters,
            limit=limit,
            offset=offset,
            ordering=ordering,
            options=options,
        )
        serialized = self.serialize_many(data, schema=schema)
        total_query = self.repo.count(filters=filters)
        total = (await session.execute(total_query)).scalar_one()
        meta = calculate_pagination(total=total, limit=limit, offset=offset)
        return PaginatedResponseSchema(meta=meta, data=serialized)

    async def build_pagination_from_queries(
        self,
        session: AsyncSession,
        *,
        data_query: Executable,
        count_query: Executable,
        limit: int,
        offset: int,
        schema: type[BaseResponseSchema] | Literal[False] | None = None,
    ) -> PaginatedResponseSchema[BaseResponseSchema | ModelType]:
        data = await session.scalars(data_query)
        serialized = self.serialize_many(data, schema=schema)
        total = (await session.execute(count_query)).scalar_one()
        meta = calculate_pagination(total=total, limit=limit, offset=offset)
        return PaginatedResponseSchema(meta=meta, data=serialized)


class RetrievalServiceMixin[PKType, ModelType: GenericBaseModel](
    SessionExecutorMixin[PKType, ModelType],
    RepositoryAccessorMixin[PKType, ModelType],
    SerializerProtocol[ModelType],
):
    async def retrieve_raw(
        self,
        session: AsyncSession,
        pk: PKType,
        *,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> ModelType:
        query = self.repo.retrieve(pk, options=options)
        return await self.execute_for_one(session, query)

    async def retrieve_one_raw_by(
        self,
        session: AsyncSession,
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
        ordering: Iterable[OrderSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> ModelType:
        query = self.repo.retrieve_one_by(filters=filters, ordering=ordering, options=options)
        return await self.execute_for_one(session, query)

    async def retrieve(
        self,
        session: AsyncSession,
        pk: PKType,
        *,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        schema: type[BaseResponseSchema] | Literal[False] | None = None,
    ) -> BaseResponseSchema | ModelType:
        entity = await self.retrieve_raw(session, pk, options=options)
        return self.serialize_one(entity, schema=schema)

    async def retrieve_all_raw_by(
        self,
        session: AsyncSession,
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
        ordering: Iterable[OrderSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> Sequence[ModelType]:
        query = self.repo.retrieve_one_by(filters=filters, ordering=ordering, options=options)
        result = await session.scalars(query)
        return result.all()


@dataclass(slots=True)
class ManyToManyRelation[ModelType: GenericBaseModel]:
    payload_field: str
    association_model: type[ModelType]
    left_key: InstrumentedAttribute[Any]
    right_key: InstrumentedAttribute[Any]
    row_factory: Callable[[Any, Any], dict[str, Any]] | None = None

    def build_row(self, owner_id: Any, target_id: Any) -> dict[str, Any]:
        if self.row_factory:
            return self.row_factory(owner_id, target_id)
        return {self.left_key.key: owner_id, self.right_key.key: target_id}


class ManyToManySyncMixin[PKType, ModelType: GenericBaseModel](
    RepositoryAccessorMixin[PKType, ModelType],
):
    many_to_many_relations: Sequence[ManyToManyRelation[Any]] = ()

    def split_m2m_payload(
        self,
        payload: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Sequence[Any]]]:
        if not self.many_to_many_relations:
            return payload, {}
        data = dict(payload)
        relation_payload: dict[str, Sequence[Any]] = {}
        for relation in self.many_to_many_relations:
            if relation.payload_field in data:
                relation_payload[relation.payload_field] = data.pop(relation.payload_field) or ()
        return data, relation_payload

    async def sync_m2m_relations(
        self,
        session: AsyncSession,
        owner_id: PKType,
        relation_payload: dict[str, Sequence[Any]],
    ) -> None:
        for relation in self.many_to_many_relations:
            if relation.payload_field not in relation_payload:
                continue
            target_ids = relation_payload[relation.payload_field]
            delete_stmt = delete(relation.association_model).where(relation.left_key == owner_id)
            await session.execute(delete_stmt)
            if not target_ids:
                continue
            rows = [relation.build_row(owner_id, target_id) for target_id in target_ids]
            await session.execute(insert(relation.association_model).values(rows))


class CreateServiceMixin[PKType, ModelType: GenericBaseModel](
    SessionExecutorMixin[PKType, ModelType],
    ManyToManySyncMixin[PKType, ModelType],
    PayloadMixin[ModelType],
    SerializerProtocol[ModelType],
):
    async def create_raw(
        self,
        session: AsyncSession,
        data: PydanticModel | dict[str, Any],
        *,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> ModelType:
        payload = self._dump_payload(data, exclude_unset=False)
        payload, relation_payload = self.split_m2m_payload(payload)
        query = self.repo.create(payload, options=options)
        entity = await self.execute_for_one(session, query)
        if relation_payload:
            await self.sync_m2m_relations(session, self._extract_pk(entity), relation_payload)
        return entity

    async def create(
        self,
        session: AsyncSession,
        data: PydanticModel | dict[str, Any],
        *,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        schema: type[BaseResponseSchema] | Literal[False] | None = None,
    ) -> BaseResponseSchema | ModelType:
        entity = await self.create_raw(session, data, options=options)
        return self.serialize_one(entity, schema=schema)


class CreateOrSkipServiceMixin[PKType, ModelType: GenericBaseModel](
    SessionExecutorMixin[PKType, ModelType],
    RepositoryAccessorMixin[PKType, ModelType],
    PayloadMixin[ModelType],
    SerializerProtocol[ModelType],
):
    async def create_or_skip_raw(
        self,
        session: AsyncSession,
        data: PydanticModel | dict[str, Any],
        *,
        conflict_columns: Sequence[InstrumentedAttribute[Any]],
        conflict_where: Iterable[FilterSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> ModelType | None:
        payload = self._dump_payload(data, exclude_unset=False)
        query = self.repo.create_or_skip(
            payload,
            conflict_columns=conflict_columns,
            conflict_where=conflict_where,
            options=options,
        )
        return await self.execute_optional(session, query)

    async def create_or_skip(
        self,
        session: AsyncSession,
        data: PydanticModel | dict[str, Any],
        *,
        conflict_columns: Sequence[InstrumentedAttribute[Any]],
        conflict_where: Iterable[FilterSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        schema: type[BaseResponseSchema] | Literal[False] | None = None,
    ) -> BaseResponseSchema | ModelType | None:
        entity = await self.create_or_skip_raw(
            session,
            data,
            conflict_columns=conflict_columns,
            conflict_where=conflict_where,
            options=options,
        )
        if entity is None:
            return None
        return self.serialize_one(entity, schema=schema)


class UpsertServiceMixin[PKType, ModelType: GenericBaseModel](
    SessionExecutorMixin[PKType, ModelType],
    ManyToManySyncMixin[PKType, ModelType],
    PayloadMixin[ModelType],
    SerializerProtocol[ModelType],
):
    async def upsert_raw(
        self,
        session: AsyncSession,
        data: PydanticModel | dict[str, Any],
        *,
        conflict_columns: Sequence[InstrumentedAttribute[Any]] | None = None,
        conflict_where: Iterable[FilterSpec[ModelType]] | None = None,
        update_only: Sequence[str] | None = None,
        update_exclude: Sequence[str] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> ModelType:
        payload = self._dump_payload(data, exclude_unset=False)
        payload, relation_payload = self.split_m2m_payload(payload)
        query = self.repo.upsert(
            payload,
            conflict_columns=conflict_columns,
            conflict_where=conflict_where,
            update_only=update_only,
            update_exclude=update_exclude,
            options=options,
        )
        entity = await self.execute_for_one(session, query)
        if relation_payload:
            await self.sync_m2m_relations(session, self._extract_pk(entity), relation_payload)
        return entity

    async def upsert(
        self,
        session: AsyncSession,
        data: PydanticModel | dict[str, Any],
        *,
        conflict_columns: Sequence[InstrumentedAttribute[Any]] | None = None,
        conflict_where: Iterable[FilterSpec[ModelType]] | None = None,
        update_only: Sequence[str] | None = None,
        update_exclude: Sequence[str] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        schema: type[BaseResponseSchema] | Literal[False] | None = None,
    ) -> BaseResponseSchema | ModelType:
        entity = await self.upsert_raw(
            session,
            data,
            conflict_columns=conflict_columns,
            conflict_where=conflict_where,
            update_only=update_only,
            update_exclude=update_exclude,
            options=options,
        )
        return self.serialize_one(entity, schema=schema)


class UpdateServiceMixin[PKType, ModelType: GenericBaseModel](
    SessionExecutorMixin[PKType, ModelType],
    ManyToManySyncMixin[PKType, ModelType],
    PayloadMixin[ModelType],
    SerializerProtocol[ModelType],
):
    async def update_raw(
        self,
        session: AsyncSession,
        pk: PKType,
        data: PydanticModel | dict[str, Any],
        *,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> ModelType:
        payload = self._dump_payload(data, exclude_unset=True)
        payload, relation_payload = self.split_m2m_payload(payload)
        query = self.repo.update(pk, payload, options=options)
        entity = await self.execute_for_one(session, query)
        if relation_payload:
            await self.sync_m2m_relations(session, self._extract_pk(entity), relation_payload)
        return entity

    async def update(
        self,
        session: AsyncSession,
        pk: PKType,
        data: PydanticModel | dict[str, Any],
        *,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        schema: type[BaseResponseSchema] | Literal[False] | None = None,
    ) -> BaseResponseSchema | ModelType:
        entity = await self.update_raw(session, pk, data, options=options)
        return self.serialize_one(entity, schema=schema)


class UpdateByFilterServiceMixin[PKType, ModelType: GenericBaseModel](
    SessionExecutorMixin[PKType, ModelType],
    RepositoryAccessorMixin[PKType, ModelType],
    PayloadMixin[ModelType],
    SerializerProtocol[ModelType],
):
    async def update_by_raw(
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
        data: PydanticModel | dict[str, Any],
        *,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> ModelType:
        payload = self._dump_payload(data, exclude_unset=True)
        query = self.repo.update_by(payload, filters=filters, options=options)
        return await self.execute_for_one(session, query)

    async def update_by(
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
        data: PydanticModel | dict[str, Any],
        *,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        schema: type[BaseResponseSchema] | Literal[False] | None = None,
    ) -> BaseResponseSchema | ModelType:
        entity = await self.update_by_raw(session, filters, data, options=options)
        return self.serialize_one(entity, schema=schema)


class DeleteServiceMixin[PKType, ModelType: GenericBaseModel](
    SessionExecutorMixin[PKType, ModelType],
    RepositoryAccessorMixin[PKType, ModelType],
):
    async def delete(self, session: AsyncSession, pk: PKType) -> None:
        await session.execute(self.repo.delete(pk))

    async def delete_by(
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
    ) -> None:
        await session.execute(self.repo.delete_by(filters=filters))


class SoftDeleteServiceMixin[PKType, ModelType: GenericBaseModel](
    DeleteServiceMixin[PKType, ModelType],
):
    repo: SoftDeleteRepositoryProtocol[PKType, ModelType]

    async def soft_delete(self, session: AsyncSession, pk: PKType) -> None:
        await session.execute(self.repo.soft_delete(pk))

    async def soft_delete_by(
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
    ) -> None:
        await session.execute(self.repo.soft_delete_by(filters=filters))


class RepositoryService[PKType, ModelType: GenericBaseModel, ResponseSchema: BaseResponseSchema](
    SerializerMixin[ModelType, ResponseSchema],
    PaginationServiceMixin[PKType, ModelType],
    RetrievalServiceMixin[PKType, ModelType],
    CreateServiceMixin[PKType, ModelType],
    CreateOrSkipServiceMixin[PKType, ModelType],
    UpsertServiceMixin[PKType, ModelType],
    UpdateServiceMixin[PKType, ModelType],
    UpdateByFilterServiceMixin[PKType, ModelType],
    DeleteServiceMixin[PKType, ModelType],
):
    """Turnkey async service that glues repository access and serialization together."""

    def __init__(self, repo: RepositoryProtocol[PKType, ModelType]) -> None:
        self.repo = repo


class SoftDeleteRepositoryService[
    PKType,
    ModelType: GenericBaseModel,
    ResponseSchema: BaseResponseSchema,
](
    RepositoryService[PKType, ModelType, ResponseSchema],
    SoftDeleteServiceMixin[PKType, ModelType],
):
    """Repository service variant that exposes soft-delete helpers."""

    def __init__(self, repo: SoftDeleteRepositoryProtocol[PKType, ModelType]) -> None:
        super().__init__(repo)
