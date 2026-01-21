from collections.abc import Iterable, Sequence
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.params import QueryParams
from notora.v2.repositories.types import (
    DEFAULT_LIMIT,
    DefaultLimit,
    FilterSpec,
    OptionSpec,
    OrderSpec,
)
from notora.v2.schemas.base import BaseResponseSchema
from notora.v2.services.mixins.accessors import RepositoryAccessorMixin
from notora.v2.services.mixins.executor import SessionExecutorMixin
from notora.v2.services.mixins.serializer import SerializerProtocol

__all__ = ['ListResponse', 'ListingServiceMixin']

ListResponse = list


class ListingServiceMixin[
    PKType,
    ModelType: GenericBaseModel,
    DetailSchema: BaseResponseSchema,
    ListSchema: BaseResponseSchema = DetailSchema,
](
    SessionExecutorMixin[PKType, ModelType],
    RepositoryAccessorMixin[PKType, ModelType],
    SerializerProtocol[ModelType, DetailSchema, ListSchema],
):
    async def list_raw(
        self,
        session: AsyncSession,
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
        limit: int | DefaultLimit | None = DEFAULT_LIMIT,
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
        return await self.execute_scalars_all(session, query)

    async def list(
        self,
        session: AsyncSession,
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
        limit: int | DefaultLimit | None = DEFAULT_LIMIT,
        offset: int = 0,
        ordering: Iterable[OrderSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        base_query: Any | None = None,
        schema: type[ListSchema] | None = None,
    ) -> ListResponse[ListSchema]:
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

    async def list_raw_params(
        self,
        session: AsyncSession,
        params: QueryParams[ModelType],
    ) -> Sequence[ModelType]:
        return await self.list_raw(
            session,
            filters=params.filters,
            limit=params.limit,
            offset=params.offset,
            ordering=params.ordering,
            options=params.options,
            base_query=params.base_query,
        )

    async def list_params(
        self,
        session: AsyncSession,
        params: QueryParams[ModelType],
        *,
        schema: type[ListSchema] | None = None,
    ) -> ListResponse[ListSchema]:
        rows = await self.list_raw_params(session, params)
        return self.serialize_many(rows, schema=schema)
