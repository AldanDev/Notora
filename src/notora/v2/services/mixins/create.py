from collections.abc import Iterable, Sequence
from typing import Any

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
    async def create_raw(
        self,
        session: AsyncSession,
        data: PydanticModel | dict[str, Any],
        *,
        actor_id: Any | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> ModelType:
        payload = self._dump_payload(data, exclude_unset=False)
        payload, relation_payload = self.split_m2m_payload(payload)
        payload = self._apply_updated_by(payload, actor_id)
        query = self.repo.create(payload, options=options)
        entity = await self.execute_for_one(session, query)
        if relation_payload:
            await self.sync_m2m_relations(session, self._extract_pk(entity), relation_payload)
        return entity

    async def create(
        self,
        session: AsyncSession,
        data: PydanticModel | dict[str, Any],
        *,
        actor_id: Any | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        schema: type[DetailSchema] | None = None,
    ) -> DetailSchema:
        entity = await self.create_raw(session, data, actor_id=actor_id, options=options)
        return self.serialize_one(entity, schema=schema)


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
    async def create_or_skip_raw(
        self,
        session: AsyncSession,
        data: PydanticModel | dict[str, Any],
        *,
        conflict_columns: Sequence[InstrumentedAttribute[Any]],
        conflict_where: Iterable[FilterSpec[ModelType]] | None = None,
        actor_id: Any | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> ModelType | None:
        payload = self._dump_payload(data, exclude_unset=False)
        payload = self._apply_updated_by(payload, actor_id)
        query = self.repo.create_or_skip(
            payload,
            conflict_columns=conflict_columns,
            conflict_where=conflict_where,
            options=options,
        )
        return await self.execute_optional(session, query)

    async def create_or_skip(
        self,
        session: AsyncSession,
        data: PydanticModel | dict[str, Any],
        *,
        conflict_columns: Sequence[InstrumentedAttribute[Any]],
        conflict_where: Iterable[FilterSpec[ModelType]] | None = None,
        actor_id: Any | None = None,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        schema: type[DetailSchema] | None = None,
    ) -> DetailSchema | None:
        entity = await self.create_or_skip_raw(
            session,
            data,
            conflict_columns=conflict_columns,
            conflict_where=conflict_where,
            actor_id=actor_id,
            options=options,
        )
        if entity is None:
            return None
        return self.serialize_one(entity, schema=schema)
