from collections.abc import Iterable
from typing import Any, overload

from sqlalchemy.ext.asyncio import AsyncSession

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.base import SoftDeleteRepositoryProtocol
from notora.v2.repositories.types import FilterSpec
from notora.v2.schemas.base import BaseResponseSchema
from notora.v2.services.mixins.accessors import RepositoryAccessorMixin
from notora.v2.services.mixins.executor import SessionExecutorMixin
from notora.v2.services.mixins.serializer import SerializerProtocol
from notora.v2.services.mixins.updated_by import UpdatedByServiceMixin

__all__ = ['DeleteServiceMixin', 'SoftDeleteServiceMixin']

class DeleteServiceMixin[
    PKType,
    ModelType: GenericBaseModel,
    DetailSchema: BaseResponseSchema,
    ListSchema: BaseResponseSchema = DetailSchema,
](
    SessionExecutorMixin[PKType, ModelType],
    RepositoryAccessorMixin[PKType, ModelType],
    UpdatedByServiceMixin[PKType, ModelType],
    SerializerProtocol[ModelType, DetailSchema, ListSchema],
):
    __type_params__: tuple[object, ...]

    async def delete_raw(
        self,
        session: AsyncSession,
        pk: PKType,
    ) -> ModelType: ...
    @overload
    async def delete(
        self,
        session: AsyncSession,
        pk: PKType,
        *,
        schema: None = ...,
    ) -> DetailSchema: ...
    @overload
    async def delete[SchemaT: BaseResponseSchema](
        self,
        session: AsyncSession,
        pk: PKType,
        *,
        schema: type[SchemaT],
    ) -> SchemaT: ...
    async def delete_by_raw(
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
    ) -> list[ModelType]: ...
    @overload
    async def delete_by(
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
        *,
        schema: None = ...,
    ) -> list[ListSchema]: ...
    @overload
    async def delete_by[SchemaT: BaseResponseSchema](
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
        *,
        schema: type[SchemaT],
    ) -> list[SchemaT]: ...

class SoftDeleteServiceMixin[
    PKType,
    ModelType: GenericBaseModel,
    DetailSchema: BaseResponseSchema,
    ListSchema: BaseResponseSchema = DetailSchema,
](
    DeleteServiceMixin[PKType, ModelType, DetailSchema, ListSchema],
):
    __type_params__: tuple[object, ...]

    repo: SoftDeleteRepositoryProtocol[PKType, ModelType]

    async def soft_delete_raw(
        self,
        session: AsyncSession,
        pk: PKType,
        *,
        actor_id: Any | None = None,
    ) -> ModelType: ...
    @overload
    async def soft_delete(
        self,
        session: AsyncSession,
        pk: PKType,
        *,
        actor_id: Any | None = None,
        schema: None = ...,
    ) -> DetailSchema: ...
    @overload
    async def soft_delete[SchemaT: BaseResponseSchema](
        self,
        session: AsyncSession,
        pk: PKType,
        *,
        actor_id: Any | None = None,
        schema: type[SchemaT],
    ) -> SchemaT: ...
    async def soft_delete_by_raw(
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
        *,
        actor_id: Any | None = None,
    ) -> list[ModelType]: ...
    @overload
    async def soft_delete_by(
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
        *,
        actor_id: Any | None = None,
        schema: None = ...,
    ) -> list[ListSchema]: ...
    @overload
    async def soft_delete_by[SchemaT: BaseResponseSchema](
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
        *,
        actor_id: Any | None = None,
        schema: type[SchemaT],
    ) -> list[SchemaT]: ...
    async def restore_raw(
        self,
        session: AsyncSession,
        pk: PKType,
        *,
        actor_id: Any | None = None,
    ) -> ModelType: ...
    @overload
    async def restore(
        self,
        session: AsyncSession,
        pk: PKType,
        *,
        actor_id: Any | None = None,
        schema: None = ...,
    ) -> DetailSchema: ...
    @overload
    async def restore[SchemaT: BaseResponseSchema](
        self,
        session: AsyncSession,
        pk: PKType,
        *,
        actor_id: Any | None = None,
        schema: type[SchemaT],
    ) -> SchemaT: ...
    async def restore_by_raw(
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
        *,
        actor_id: Any | None = None,
    ) -> list[ModelType]: ...
    @overload
    async def restore_by(
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
        *,
        actor_id: Any | None = None,
        schema: None = ...,
    ) -> list[ListSchema]: ...
    @overload
    async def restore_by[SchemaT: BaseResponseSchema](
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
        *,
        actor_id: Any | None = None,
        schema: type[SchemaT],
    ) -> list[SchemaT]: ...
