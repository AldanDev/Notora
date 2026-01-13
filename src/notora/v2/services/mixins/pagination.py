from collections.abc import Iterable
from typing import Literal

from sqlalchemy import Executable
from sqlalchemy.ext.asyncio import AsyncSession

from notora.v2.models.base import GenericBaseModel
from notora.v2.schemas.base import (
    BaseResponseSchema,
    PaginatedResponseSchema,
    PaginationMetaSchema,
)

from ...repositories.types import FilterSpec, OptionSpec, OrderSpec
from .listing import ListingServiceMixin


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
        meta = PaginationMetaSchema.calculate(total=total, limit=limit, offset=offset)
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
        meta = PaginationMetaSchema.calculate(total=total, limit=limit, offset=offset)
        return PaginatedResponseSchema(meta=meta, data=serialized)
