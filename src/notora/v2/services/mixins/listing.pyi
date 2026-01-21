from collections.abc import Iterable, Sequence
from typing import Any, overload

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

type ListResponse[ListSchema: BaseResponseSchema] = list[ListSchema]

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
    __type_params__: tuple[object, ...]

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
    ) -> Sequence[ModelType]: ...
    @overload
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
        schema: None = ...,
    ) -> ListResponse[ListSchema]: ...
    @overload
    async def list[SchemaT: BaseResponseSchema](
        self,
        session: AsyncSession,
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
        limit: int | DefaultLimit | None = DEFAULT_LIMIT,
        offset: int = 0,
        ordering: Iterable[OrderSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        base_query: Any | None = None,
        schema: type[SchemaT],
    ) -> ListResponse[SchemaT]: ...
    async def list_raw_params(
        self,
        session: AsyncSession,
        params: QueryParams[ModelType],
    ) -> Sequence[ModelType]: ...
    @overload
    async def list_params(
        self,
        session: AsyncSession,
        params: QueryParams[ModelType],
        *,
        schema: None = ...,
    ) -> ListResponse[ListSchema]: ...
    @overload
    async def list_params[SchemaT: BaseResponseSchema](
        self,
        session: AsyncSession,
        params: QueryParams[ModelType],
        *,
        schema: type[SchemaT],
    ) -> ListResponse[SchemaT]: ...
