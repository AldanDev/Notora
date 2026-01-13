import logging
import re
from collections.abc import Iterable, Sequence
from typing import Any, ClassVar, overload
from uuid import UUID

from pydantic import BaseModel as BaseSchema
from sqlalchemy import Executable, ScalarResult, ScalarSelect, Select, exc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.selectable import TypedReturnsRows

from notora.utils.time import now_without_tz
from notora.utils.validation import validate_exclusive_presence
from notora.v1.exceptions.common import AlreadyExistsError, FKNotFoundError, NotFoundError
from notora.v1.models.base import BaseModel, GenericBaseModel
from notora.v1.persistence.repos.base import BaseRepo, SoftDeletableRepo
from notora.v1.schemas.base import (
    BaseResponseSchema,
    Filter,
    OrderBy,
    OrFilterGroup,
    PaginatedResponseSchema,
    PaginationMetaSchema,
    SetUpdatedBySchema,
)

log = logging.getLogger(__name__)

type Filters = Filter | OrFilterGroup


class BaseService[  # noqa: PLR0904
    PKType,
    ModelClass: GenericBaseModel,
    ModelResponseSchema: BaseResponseSchema,
]:
    response_schema: type[ModelResponseSchema]
    repo: BaseRepo[PKType, ModelClass]

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

    def __init__(self, repo: BaseRepo[PKType, ModelClass]) -> None:
        self.repo = repo

    def serialize(self, db_result: ModelClass) -> ModelResponseSchema:
        return self.response_schema.model_validate(db_result)

    def serialize_many(self, db_result: Iterable[ModelClass]) -> list[ModelResponseSchema]:
        return [self.serialize(item) for item in db_result]

    async def list_raw(
        self,
        session: AsyncSession,
        filters: Iterable[Filters] = (),
        limit: int = 20,
        offset: int = 0,
        order_by: Iterable[OrderBy] = (),
        base_query: Select[tuple[Any]] | None = None,
    ) -> Iterable[ModelClass]:
        query = self.repo.list_(
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=order_by,
            base_query=base_query,
        )
        return await session.scalars(query)

    async def list_(
        self,
        session: AsyncSession,
        filters: Iterable[Filters] = (),
        limit: int = 20,
        offset: int = 0,
        order_by: Iterable[OrderBy] = (),
        base_query: Select[tuple[Any]] | None = None,
    ) -> list[ModelResponseSchema]:
        results = await self.list_raw(
            session=session,
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=order_by,
            base_query=base_query,
        )
        return self.serialize_many(results)

    async def bulk_create(
        self,
        db_session: AsyncSession,
        data: Sequence[BaseSchema],
    ) -> list[ModelResponseSchema]:
        query = self.repo.bulk_create([item.model_dump() for item in data])
        try:
            results = await db_session.scalars(query)
        except exc.IntegrityError as ex:
            raise self.__reraise_integrity_error(ex) from ex
        return self.serialize_many(results)

    @overload
    async def upsert(
        self,
        db_session: AsyncSession,
        data: BaseSchema,
        *,
        update_include_fields: Iterable[str] | None = None,
        index_elements: Iterable[InstrumentedAttribute[Any]] | None = None,
    ) -> ModelResponseSchema: ...

    @overload
    async def upsert(
        self,
        db_session: AsyncSession,
        data: BaseSchema,
        *,
        update_exclude_fields: Iterable[str] | None = None,
        index_elements: Iterable[InstrumentedAttribute[Any]] | None = None,
    ) -> ModelResponseSchema: ...

    async def upsert(
        self,
        db_session: AsyncSession,
        data: BaseSchema,
        *,
        update_include_fields: Iterable[str] | None = None,
        update_exclude_fields: Iterable[str] | None = None,
        index_elements: Iterable[InstrumentedAttribute[Any]] | None = None,
    ) -> ModelResponseSchema:
        validate_exclusive_presence(update_include_fields, update_exclude_fields)
        if update_include_fields is not None:
            result = await self.upsert_raw(
                db_session=db_session,
                data=data,
                update_include_fields=update_include_fields,
                index_elements=index_elements,
            )
        elif update_exclude_fields is not None:
            result = await self.upsert_raw(
                db_session=db_session,
                data=data,
                update_exclude_fields=update_exclude_fields,
                index_elements=index_elements,
            )
        return self.serialize(result)  # pyright: ignore [reportArgumentType], doesn't do conditional narrowing

    @overload
    async def upsert_raw(
        self,
        db_session: AsyncSession,
        data: BaseSchema,
        *,
        update_include_fields: Iterable[str] | None = None,
        index_elements: Iterable[InstrumentedAttribute[Any]] | None = None,
    ) -> ModelClass: ...

    @overload
    async def upsert_raw(
        self,
        db_session: AsyncSession,
        data: BaseSchema,
        *,
        update_exclude_fields: Iterable[str] | None = None,
        index_elements: Iterable[InstrumentedAttribute[Any]] | None = None,
    ) -> ModelClass: ...

    async def upsert_raw(
        self,
        db_session: AsyncSession,
        data: BaseSchema,
        *,
        update_include_fields: Iterable[str] | None = None,
        update_exclude_fields: Iterable[str] | None = None,
        index_elements: Iterable[InstrumentedAttribute[Any]] | None = None,
    ) -> ModelClass:
        validate_exclusive_presence(update_include_fields, update_exclude_fields)
        if update_include_fields is not None:
            query = self.repo.upsert(
                data=data.model_dump(),
                update_include_fields=update_include_fields,
                index_elements=index_elements,
            )
        elif update_exclude_fields is not None:
            query = self.repo.upsert(
                data=data.model_dump(),
                update_exclude_fields=update_exclude_fields,
                index_elements=index_elements,
            )
        result = await self.execute_for_one(db_session, query)
        return result

    async def paginate(
        self,
        session: AsyncSession,
        filters: Iterable[Filters] = (),
        limit: int = 20,
        offset: int = 0,
        order_by: Iterable[OrderBy] = (),
    ) -> PaginatedResponseSchema[ModelResponseSchema]:
        data = await self.list_(
            session=session,
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=order_by,
        )
        meta = await self.get_filters_pagination_info(
            session=session,
            filters=filters,
            limit=limit,
            offset=offset,
        )
        return PaginatedResponseSchema(meta=meta, data=data)

    async def get_filters_pagination_info(
        self,
        session: AsyncSession,
        filters: Iterable[Filters] = (),
        limit: int = 20,
        offset: int = 0,
    ) -> PaginationMetaSchema:
        query = self.repo.number_of_records(filters)
        total = (await session.execute(query)).scalar_one()
        return PaginationMetaSchema.calculate(total, limit, offset)

    async def build_pagination_from_queries(
        self,
        db_session: AsyncSession,
        data_query: Executable,
        count_query: Executable,
        limit: int,
        offset: int,
    ) -> PaginatedResponseSchema[ModelResponseSchema]:
        data = self.serialize_many(await db_session.scalars(data_query))
        count = (await db_session.execute(count_query)).scalar_one()
        meta = PaginationMetaSchema.calculate(
            total=count,
            limit=limit,
            offset=offset,
        )
        return PaginatedResponseSchema(meta=meta, data=data)

    async def create(
        self,
        session: AsyncSession,
        data: BaseSchema,
    ) -> ModelResponseSchema:
        result = await self.create_raw(session, data)
        return self.serialize(result)

    async def create_raw(
        self,
        session: AsyncSession,
        data: BaseSchema,
    ) -> ModelClass:
        query = self.repo.create(data.model_dump())
        result = await self.execute_for_one(session, query)
        return result

    async def create_raw_or_skip(
        self,
        db_session: AsyncSession,
        data: BaseSchema,
        index_elements: Iterable[InstrumentedAttribute[Any]],
    ) -> ModelClass | None:
        query = self.repo.create_or_skip(data.model_dump(), index_elements)
        result = await self.execute(db_session, query)
        return result

    async def retrieve(self, session: AsyncSession, entity_id: PKType) -> ModelResponseSchema:
        entity = await self.retrieve_raw(session, entity_id)
        return self.serialize(entity)

    async def retrieve_raw(self, session: AsyncSession, entity_id: PKType) -> ModelClass:
        query = self.repo.retrieve(entity_id)
        result = await self.execute_for_one(session, query)
        return result

    async def retrieve_one_by(
        self,
        session: AsyncSession,
        filters: Iterable[Filters],
    ) -> ModelResponseSchema:
        data = await self.retrieve_one_raw_by(session, filters)
        return self.serialize(data)

    async def retrieve_one_raw_by(
        self,
        session: AsyncSession,
        filters: Iterable[Filters],
    ) -> ModelClass:
        query = self.repo.retrieve_by(filters)
        result = await self.execute_for_one(session, query)
        return result

    async def retrieve_all_by(
        self,
        db_session: AsyncSession,
        filters: Iterable[Filters] = (),
        order_by: Iterable[OrderBy] = (),
    ) -> list[ModelResponseSchema]:
        results = await self.retrieve_all_raw_by(db_session, filters, order_by)
        return self.serialize_many(results)

    async def retrieve_all_raw_by(
        self,
        db_session: AsyncSession,
        filters: Iterable[Filters] = (),
        order_by: Iterable[OrderBy] = (),
    ) -> ScalarResult[ModelClass]:
        query = self.repo.retrieve_by(filters, order_by)
        result = await db_session.scalars(query)
        return result

    async def hard_delete(self, session: AsyncSession, entity_id: PKType) -> None:
        query = self.repo.hard_delete(entity_id)
        await session.execute(query)

    async def update(
        self,
        db_session: AsyncSession,
        data: BaseSchema,
        entity_id: PKType | ScalarSelect[PKType],
    ) -> ModelResponseSchema:
        entity = await self.update_raw(db_session, data, entity_id)
        return self.serialize(entity)

    async def update_raw(
        self,
        db_session: AsyncSession,
        data: BaseSchema,
        entity_id: PKType | ScalarSelect[PKType],
    ) -> ModelClass:
        query = self.repo.update(entity_id, data.model_dump(exclude_unset=True))
        result = await self.execute_for_one(db_session, query)
        return result

    async def update_one_raw_by(
        self,
        db_session: AsyncSession,
        data: BaseSchema,
        filters: Iterable[Filters],
    ) -> ModelClass:
        query = self.repo.update_by(data.model_dump(exclude_unset=True), filters)
        result = await self.execute_for_one(db_session, query)
        return result

    async def set_updated_by(
        self,
        db_session: AsyncSession,
        updated_by: UUID,
        entity_id: PKType | ScalarSelect[PKType],
    ) -> ModelResponseSchema:
        return await self.update(
            db_session,
            SetUpdatedBySchema(updated_at=now_without_tz(), updated_by=updated_by),
            entity_id,
        )

    async def execute_for_one[T](
        self,
        db_session: AsyncSession,
        query: TypedReturnsRows[tuple[T]],
    ) -> T:
        result = await self.execute(db_session, query)
        if result is None:
            raise NotFoundError[PKType](self._not_found_error)
        return result

    async def execute[T](
        self,
        db_session: AsyncSession,
        query: TypedReturnsRows[tuple[T]],
    ) -> T | None:
        try:
            entity = await db_session.execute(query)
        except exc.IntegrityError as ex:
            raise self.__reraise_integrity_error(ex) from ex
        result = entity.unique().scalar_one_or_none()
        return result

    def __reraise_integrity_error(self, ex: exc.IntegrityError) -> Exception:
        if result := self._fk_constraint_pattern.match(ex.args[0]):
            fk_name = result.group('fk_name')
            table_name = result.group('table_name')
            msg = 'Related object not found.'
            return FKNotFoundError(
                self._fk_violation_errors.get(fk_name, msg),
                fk_name=fk_name,
                table_name=table_name,
            )
        if result := self._unique_constraint_pattern.match(ex.args[0]):
            constraint = result.group('name')
            msg = 'Entity already exists.'
            return AlreadyExistsError(
                self._unique_violation_errors.get(constraint, msg),
                constraint_name=constraint,
            )
        return ex


class SoftDeletableService[
    PKType,
    ModelClass: BaseModel,
    ModelResponseSchema: BaseResponseSchema,
](BaseService[PKType, ModelClass, ModelResponseSchema]):
    def __init__(self, repo: SoftDeletableRepo[PKType, ModelClass]) -> None:
        super().__init__(repo)
        self.repo: SoftDeletableRepo[PKType, ModelClass] = repo

    async def soft_delete(self, db_session: AsyncSession, entity_id: PKType) -> ModelClass:
        query = self.repo.soft_delete(entity_id)
        result = await self.execute_for_one(db_session, query)
        return result

    async def soft_delete_one_by(
        self,
        db_session: AsyncSession,
        filters: Iterable[Filters],
    ) -> ModelClass:
        query = self.repo.soft_delete_by(filters)
        result = await self.execute_for_one(db_session, query)
        return result

    async def soft_delete_all_raw_by(
        self,
        db_session: AsyncSession,
        filters: Iterable[Filters],
    ) -> Iterable[ModelClass]:
        query = self.repo.soft_delete_by(filters)
        result = await db_session.scalars(query)
        return result
