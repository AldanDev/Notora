from collections.abc import Iterable, Sequence
from typing import Any, overload

from pydantic import BaseModel as PydanticModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.types import FilterSpec, OptionSpec
from notora.v2.schemas.base import BaseResponseSchema
from notora.v2.services.mixins.accessors import RepositoryAccessorMixin
from notora.v2.services.mixins.executor import SessionExecutorMixin
from notora.v2.services.mixins.m2m import ManyToManySyncMixin
from notora.v2.services.mixins.payload import PayloadMixin
from notora.v2.services.mixins.serializer import SerializerProtocol
from notora.v2.services.mixins.updated_by import UpdatedByServiceMixin

__all__ = ['CreateOrSkipServiceMixin', 'CreateServiceMixin']

class CreateServiceMixin[
    PKType,
    ModelType: GenericBaseModel,
    DetailSchema: BaseResponseSchema,
    ListSchema: BaseResponseSchema = DetailSchema,
](
    ManyToManySyncMixin[PKType, ModelType],
    UpdatedByServiceMixin[PKType, ModelType],
    PayloadMixin[ModelType],
    SerializerProtocol[ModelType, DetailSchema, ListSchema],
):
    __type_params__: tuple[object, ...]

    async def create_raw(
        self,
        session: AsyncSession,
        data: PydanticModel | dict[str, Any],
        *,
        actor_id: Any | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> ModelType: ...
    @overload
    async def create(
        self,
        session: AsyncSession,
        data: PydanticModel | dict[str, Any],
        *,
        actor_id: Any | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        schema: None = ...,
    ) -> DetailSchema: ...
    @overload
    async def create[SchemaT: BaseResponseSchema](
        self,
        session: AsyncSession,
        data: PydanticModel | dict[str, Any],
        *,
        actor_id: Any | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        schema: type[SchemaT],
    ) -> SchemaT: ...

class CreateOrSkipServiceMixin[
    PKType,
    ModelType: GenericBaseModel,
    DetailSchema: BaseResponseSchema,
    ListSchema: BaseResponseSchema = DetailSchema,
](
    SessionExecutorMixin[PKType, ModelType],
    RepositoryAccessorMixin[PKType, ModelType],
    UpdatedByServiceMixin[PKType, ModelType],
    PayloadMixin[ModelType],
    SerializerProtocol[ModelType, DetailSchema, ListSchema],
):
    __type_params__: tuple[object, ...]

    async def create_or_skip_raw(
        self,
        session: AsyncSession,
        data: PydanticModel | dict[str, Any],
        *,
        conflict_columns: Sequence[InstrumentedAttribute[Any]],
        conflict_where: Iterable[FilterSpec[ModelType]] | None = None,
        actor_id: Any | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> ModelType | None: ...
    @overload
    async def create_or_skip(
        self,
        session: AsyncSession,
        data: PydanticModel | dict[str, Any],
        *,
        conflict_columns: Sequence[InstrumentedAttribute[Any]],
        conflict_where: Iterable[FilterSpec[ModelType]] | None = None,
        actor_id: Any | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        schema: None = ...,
    ) -> DetailSchema | None: ...
    @overload
    async def create_or_skip[SchemaT: BaseResponseSchema](
        self,
        session: AsyncSession,
        data: PydanticModel | dict[str, Any],
        *,
        conflict_columns: Sequence[InstrumentedAttribute[Any]],
        conflict_where: Iterable[FilterSpec[ModelType]] | None = None,
        actor_id: Any | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        schema: type[SchemaT],
    ) -> SchemaT | None: ...
