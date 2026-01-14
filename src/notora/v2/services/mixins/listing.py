from collections.abc import Iterable, Sequence
from typing import Any, Literal

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
from notora.v2.services.mixins.serializer import SerializerProtocol

type ListResponse[ModelType: GenericBaseModel] = list[BaseResponseSchema] | list[ModelType]


class ListingServiceMixin[PKType, ModelType: GenericBaseModel](
    RepositoryAccessorMixin[PKType, ModelType],
    SerializerProtocol[ModelType],
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
        result = await session.scalars(query)
        return result.all()

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
        schema: type[BaseResponseSchema] | Literal[False] | None = None,
    ) -> ListResponse[ModelType]:
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
        schema: type[BaseResponseSchema] | Literal[False] | None = None,
    ) -> ListResponse[ModelType]:
        rows = await self.list_raw_params(session, params)
        return self.serialize_many(rows, schema=schema)
