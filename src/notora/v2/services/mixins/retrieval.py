from collections.abc import Iterable, Sequence
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from notora.v2.models.base import GenericBaseModel
from notora.v2.schemas.base import BaseResponseSchema

from ...repositories.types import FilterSpec, OptionSpec, OrderSpec
from .accessors import RepositoryAccessorMixin
from .executor import SessionExecutorMixin
from .serializer import SerializerProtocol


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
