from collections.abc import Iterable
from typing import Any

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
    async def update_raw(
        self,
        session: AsyncSession,
        pk: PKType,
        data: PydanticModel | dict[str, Any],
        *,
        actor_id: Any | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> ModelType:
        payload = self._dump_payload(data, exclude_unset=True)
        payload, relation_payload = self.split_m2m_payload(payload)
        payload = self._apply_updated_by(payload, actor_id)
        query = self.repo.update(pk, payload, options=options)
        entity = await self.execute_for_one(session, query)
        if relation_payload:
            await self.sync_m2m_relations(session, self._extract_pk(entity), relation_payload)
        return entity

    async def update(
        self,
        session: AsyncSession,
        pk: PKType,
        data: PydanticModel | dict[str, Any],
        *,
        actor_id: Any | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        schema: type[DetailSchema] | None = None,
    ) -> DetailSchema:
        entity = await self.update_raw(session, pk, data, actor_id=actor_id, options=options)
        return self.serialize_one(entity, schema=schema)


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
    async def update_by_raw(
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
        data: PydanticModel | dict[str, Any],
        *,
        actor_id: Any | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> ModelType:
        payload = self._dump_payload(data, exclude_unset=True)
        payload = self._apply_updated_by(payload, actor_id)
        query = self.repo.update_by(payload, filters=filters, options=options)
        return await self.execute_for_one(session, query)

    async def update_by(
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
        data: PydanticModel | dict[str, Any],
        *,
        actor_id: Any | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        schema: type[DetailSchema] | None = None,
    ) -> DetailSchema:
        entity = await self.update_by_raw(
            session,
            filters,
            data,
            actor_id=actor_id,
            options=options,
        )
        return self.serialize_one(entity, schema=schema)
