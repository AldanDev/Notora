from collections.abc import Iterable
from typing import Any, overload

from pydantic import BaseModel as PydanticModel
from sqlalchemy.ext.asyncio import AsyncSession

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.types import FilterSpec, OptionSpec
from notora.v2.schemas.base import BaseResponseSchema
from notora.v2.services.mixins.accessors import RepositoryAccessorMixin
from notora.v2.services.mixins.executor import SessionExecutorMixin
from notora.v2.services.mixins.m2m import ManyToManySyncMixin
from notora.v2.services.mixins.payload import PayloadMixin
from notora.v2.services.mixins.serializer import SerializerProtocol
from notora.v2.services.mixins.updated_by import UpdatedByServiceMixin

__all__ = ['UpdateByFilterServiceMixin', 'UpdateServiceMixin']

class UpdateServiceMixin[
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

    async def update_raw(
        self,
        session: AsyncSession,
        pk: PKType,
        data: PydanticModel | dict[str, Any],
        *,
        actor_id: Any | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> ModelType: ...
    @overload
    async def update(
        self,
        session: AsyncSession,
        pk: PKType,
        data: PydanticModel | dict[str, Any],
        *,
        actor_id: Any | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        schema: None = ...,
    ) -> DetailSchema: ...
    @overload
    async def update[SchemaT: BaseResponseSchema](
        self,
        session: AsyncSession,
        pk: PKType,
        data: PydanticModel | dict[str, Any],
        *,
        actor_id: Any | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        schema: type[SchemaT],
    ) -> SchemaT: ...

class UpdateByFilterServiceMixin[
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

    async def update_by_raw(
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
        data: PydanticModel | dict[str, Any],
        *,
        actor_id: Any | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> ModelType: ...
    @overload
    async def update_by(
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
        data: PydanticModel | dict[str, Any],
        *,
        actor_id: Any | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        schema: None = ...,
    ) -> DetailSchema: ...
    @overload
    async def update_by[SchemaT: BaseResponseSchema](
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
        data: PydanticModel | dict[str, Any],
        *,
        actor_id: Any | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        schema: type[SchemaT],
    ) -> SchemaT: ...
