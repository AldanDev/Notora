from collections.abc import Iterable
from typing import Any, overload

from sqlalchemy import Executable
from sqlalchemy.ext.asyncio import AsyncSession

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.params import PaginationParams
from notora.v2.repositories.types import FilterSpec, OptionSpec, OrderSpec
from notora.v2.schemas.base import (
    BaseResponseSchema,
    PaginatedResponseSchema,
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
    __type_params__: tuple[object, ...]

    @overload
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
        schema: None = ...,
    ) -> PaginatedResponseSchema[ListSchema]: ...
    @overload
    async def paginate[SchemaT: BaseResponseSchema](
        self,
        session: AsyncSession,
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
        limit: int = 20,
        offset: int = 0,
        ordering: Iterable[OrderSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        base_query: Any | None = None,
        schema: type[SchemaT],
    ) -> PaginatedResponseSchema[SchemaT]: ...
    @overload
    async def paginate_from_queries(
        self,
        session: AsyncSession,
        *,
        data_query: Executable,
        count_query: Executable,
        limit: int,
        offset: int,
        schema: None = ...,
    ) -> PaginatedResponseSchema[ListSchema]: ...
    @overload
    async def paginate_from_queries[SchemaT: BaseResponseSchema](
        self,
        session: AsyncSession,
        *,
        data_query: Executable,
        count_query: Executable,
        limit: int,
        offset: int,
        schema: type[SchemaT],
    ) -> PaginatedResponseSchema[SchemaT]: ...
    @overload
    async def paginate_params(
        self,
        session: AsyncSession,
        params: PaginationParams[ModelType],
        *,
        schema: None = ...,
    ) -> PaginatedResponseSchema[ListSchema]: ...
    @overload
    async def paginate_params[SchemaT: BaseResponseSchema](
        self,
        session: AsyncSession,
        params: PaginationParams[ModelType],
        *,
        schema: type[SchemaT],
    ) -> PaginatedResponseSchema[SchemaT]: ...
