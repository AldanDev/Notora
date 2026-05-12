from collections.abc import Iterable
from typing import Any

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
    async def delete_raw(self, session: AsyncSession, pk: PKType) -> ModelType:
        return await self.execute_for_one(session, self.repo.delete(pk))

    async def delete(
        self,
        session: AsyncSession,
        pk: PKType,
        *,
        schema: type[DetailSchema] | None = None,
    ) -> DetailSchema:
        entity = await self.delete_raw(session, pk)
        return self.serialize_one(entity, schema=schema)

    async def delete_by_raw(
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
    ) -> list[ModelType]:
        return await self.execute_for_many(session, self.repo.delete_by(filters=filters))

    async def delete_by(
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
        *,
        schema: type[ListSchema] | None = None,
    ) -> list[ListSchema]:
        entities = await self.delete_by_raw(session, filters)
        return self.serialize_many(entities, schema=schema)


class SoftDeleteServiceMixin[
    PKType,
    ModelType: GenericBaseModel,
    DetailSchema: BaseResponseSchema,
    ListSchema: BaseResponseSchema = DetailSchema,
](
    DeleteServiceMixin[PKType, ModelType, DetailSchema, ListSchema],
):
    repo: SoftDeleteRepositoryProtocol[PKType, ModelType]

    async def soft_delete_raw(
        self,
        session: AsyncSession,
        pk: PKType,
        *,
        actor_id: Any | None = None,
    ) -> ModelType:
        additional_payload = self._apply_updated_by({}, actor_id) or None
        return await self.execute_for_one(
            session,
            self.repo.soft_delete(pk, additional_payload=additional_payload),
        )

    async def soft_delete(
        self,
        session: AsyncSession,
        pk: PKType,
        *,
        actor_id: Any | None = None,
        schema: type[DetailSchema] | None = None,
    ) -> DetailSchema:
        entity = await self.soft_delete_raw(session, pk, actor_id=actor_id)
        return self.serialize_one(entity, schema=schema)

    async def soft_delete_by_raw(
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
        *,
        actor_id: Any | None = None,
    ) -> list[ModelType]:
        additional_payload = self._apply_updated_by({}, actor_id) or None
        return await self.execute_for_many(
            session,
            self.repo.soft_delete_by(
                filters=filters,
                additional_payload=additional_payload,
            ),
        )

    async def soft_delete_by(
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
        *,
        actor_id: Any | None = None,
        schema: type[ListSchema] | None = None,
    ) -> list[ListSchema]:
        entities = await self.soft_delete_by_raw(session, filters, actor_id=actor_id)
        return self.serialize_many(entities, schema=schema)

    async def restore_raw(
        self,
        session: AsyncSession,
        pk: PKType,
        *,
        actor_id: Any | None = None,
    ) -> ModelType:
        additional_payload = self._apply_updated_by({}, actor_id) or None
        return await self.execute_for_one(
            session,
            self.repo.restore(pk, additional_payload=additional_payload),
        )

    async def restore(
        self,
        session: AsyncSession,
        pk: PKType,
        *,
        actor_id: Any | None = None,
        schema: type[DetailSchema] | None = None,
    ) -> DetailSchema:
        entity = await self.restore_raw(session, pk, actor_id=actor_id)
        return self.serialize_one(entity, schema=schema)

    async def restore_by_raw(
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
        *,
        actor_id: Any | None = None,
    ) -> list[ModelType]:
        additional_payload = self._apply_updated_by({}, actor_id) or None
        return await self.execute_for_many(
            session,
            self.repo.restore_by(
                filters=filters,
                additional_payload=additional_payload,
            ),
        )

    async def restore_by(
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
        *,
        actor_id: Any | None = None,
        schema: type[ListSchema] | None = None,
    ) -> list[ListSchema]:
        entities = await self.restore_by_raw(session, filters, actor_id=actor_id)
        return self.serialize_many(entities, schema=schema)
