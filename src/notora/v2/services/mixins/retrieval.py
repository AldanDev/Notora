from collections.abc import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.types import FilterSpec, OptionSpec, OrderSpec
from notora.v2.schemas.base import BaseResponseSchema
from notora.v2.services.mixins.accessors import RepositoryAccessorMixin
from notora.v2.services.mixins.executor import SessionExecutorMixin
from notora.v2.services.mixins.serializer import SerializerProtocol

__all__ = ['RetrievalServiceMixin']


class RetrievalServiceMixin[
    PKType,
    ModelType: GenericBaseModel,
    DetailSchema: BaseResponseSchema,
    ListSchema: BaseResponseSchema = DetailSchema,
](
    SessionExecutorMixin[PKType, ModelType],
    RepositoryAccessorMixin[PKType, ModelType],
    SerializerProtocol[ModelType, DetailSchema, ListSchema],
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

    async def retrieve_one_by_raw(
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
        schema: type[DetailSchema] | None = None,
    ) -> DetailSchema:
        entity = await self.retrieve_raw(session, pk, options=options)
        return self.serialize_one(entity, schema=schema)

    async def retrieve_one_by(
        self,
        session: AsyncSession,
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
        ordering: Iterable[OrderSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        schema: type[DetailSchema] | None = None,
    ) -> DetailSchema:
        entity = await self.retrieve_one_by_raw(
            session,
            filters=filters,
            ordering=ordering,
            options=options,
        )
        return self.serialize_one(entity, schema=schema)
