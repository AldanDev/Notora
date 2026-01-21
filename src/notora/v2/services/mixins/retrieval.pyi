from collections.abc import Iterable
from typing import overload

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
    __type_params__: tuple[object, ...]

    async def retrieve_raw(
        self,
        session: AsyncSession,
        pk: PKType,
        *,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> ModelType: ...
    async def retrieve_one_by_raw(
        self,
        session: AsyncSession,
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
        ordering: Iterable[OrderSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> ModelType: ...
    @overload
    async def retrieve(
        self,
        session: AsyncSession,
        pk: PKType,
        *,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        schema: None = ...,
    ) -> DetailSchema: ...
    @overload
    async def retrieve[SchemaT: BaseResponseSchema](
        self,
        session: AsyncSession,
        pk: PKType,
        *,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        schema: type[SchemaT],
    ) -> SchemaT: ...
    @overload
    async def retrieve_one_by(
        self,
        session: AsyncSession,
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
        ordering: Iterable[OrderSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        schema: None = ...,
    ) -> DetailSchema: ...
    @overload
    async def retrieve_one_by[SchemaT: BaseResponseSchema](
        self,
        session: AsyncSession,
        *,
        filters: Iterable[FilterSpec[ModelType]] | None = None,
        ordering: Iterable[OrderSpec[ModelType]] | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        schema: type[SchemaT],
    ) -> SchemaT: ...
