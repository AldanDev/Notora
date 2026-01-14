from collections.abc import Iterable
from typing import Any, Literal

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
        base_query: Any | None = None,
        schema: type[BaseResponseSchema] | Literal[False] | None = None,
    ) -> 'PaginatedResponseSchema[BaseResponseSchema | ModelType]':
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
        total = (await session.execute(total_query)).scalar_one()
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
        schema: type[BaseResponseSchema] | Literal[False] | None = None,
    ) -> 'PaginatedResponseSchema[BaseResponseSchema | ModelType]':
        data = (await session.scalars(data_query)).all()
        serialized = self.serialize_many(data, schema=schema)
        total = (await session.execute(count_query)).scalar_one()
        meta = PaginationMetaSchema.calculate(total=total, limit=limit, offset=offset)
        return PaginatedResponseSchema(meta=meta, data=serialized)

    async def paginate_params(
        self,
        session: AsyncSession,
        params: PaginationParams[ModelType],
        *,
        schema: type[BaseResponseSchema] | Literal[False] | None = None,
    ) -> 'PaginatedResponseSchema[BaseResponseSchema | ModelType]':
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
