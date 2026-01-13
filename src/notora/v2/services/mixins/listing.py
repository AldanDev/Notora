from collections.abc import Iterable, Sequence
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from notora.v2.models.base import GenericBaseModel
from notora.v2.schemas.base import BaseResponseSchema

from ...repositories.types import FilterSpec, OptionSpec, OrderSpec
from .accessors import RepositoryAccessorMixin
from .serializer import SerializerProtocol


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
