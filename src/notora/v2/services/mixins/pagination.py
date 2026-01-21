from collections.abc import Iterable
from typing import Any

from sqlalchemy import Executable
from sqlalchemy.ext.asyncio import AsyncSession

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.params import PaginationParams
from notora.v2.repositories.types import FilterSpec, OptionSpec, OrderSpec
from notora.v2.schemas.base import (
    BaseResponseSchema,
    PaginatedResponseSchema,
    PaginationMetaSchema,
)
from notora.v2.services.mixins.listing import ListingServiceMixin

__all__ = ['PaginationServiceMixin']


class PaginationServiceMixin[
    PKType,
    ModelType: GenericBaseModel,
    DetailSchema: BaseResponseSchema,
    ListSchema: BaseResponseSchema = DetailSchema,
](
    ListingServiceMixin[PKType, ModelType, DetailSchema, ListSchema],
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
        base_query: Any | None = None,
        schema: type[ListSchema] | None = None,
    ) -> 'PaginatedResponseSchema[ListSchema]':
        data = await self.list_raw(
            session,
            filters=filters,
            limit=limit,
            offset=offset,
            ordering=ordering,
            options=options,
            base_query=base_query,
        )
        serialized = self.serialize_many(data, schema=schema)
        total_query = self.repo.count(filters=filters)
        total: int = await self.execute_scalar_one(session, total_query)
        meta = PaginationMetaSchema.calculate(total=total, limit=limit, offset=offset)
        return PaginatedResponseSchema(meta=meta, data=serialized)

    async def paginate_from_queries(
        self,
        session: AsyncSession,
        *,
        data_query: Executable,
        count_query: Executable,
        limit: int,
        offset: int,
        schema: type[ListSchema] | None = None,
    ) -> 'PaginatedResponseSchema[ListSchema]':
        data: list[ModelType] = await self.execute_scalars_all(session, data_query)
        serialized = self.serialize_many(data, schema=schema)
        total: int = await self.execute_scalar_one(session, count_query)
        meta = PaginationMetaSchema.calculate(total=total, limit=limit, offset=offset)
        return PaginatedResponseSchema(meta=meta, data=serialized)

    async def paginate_params(
        self,
        session: AsyncSession,
        params: PaginationParams[ModelType],
        *,
        schema: type[ListSchema] | None = None,
    ) -> 'PaginatedResponseSchema[ListSchema]':
        return await self.paginate(
            session,
            filters=params.filters,
            limit=params.limit,
            offset=params.offset,
            ordering=params.ordering,
            options=params.options,
            base_query=params.base_query,
            schema=schema,
        )
