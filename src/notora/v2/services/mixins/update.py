from collections.abc import Iterable
from typing import Any, Literal

from pydantic import BaseModel as PydanticModel
from sqlalchemy.ext.asyncio import AsyncSession

from notora.v2.models.base import GenericBaseModel
from notora.v2.schemas.base import BaseResponseSchema

from ...repositories.types import FilterSpec, OptionSpec
from .accessors import RepositoryAccessorMixin
from .executor import SessionExecutorMixin
from .m2m import ManyToManySyncMixin
from .payload import PayloadMixin
from .serializer import SerializerProtocol


class UpdateServiceMixin[PKType, ModelType: GenericBaseModel](
    SessionExecutorMixin[PKType, ModelType],
    ManyToManySyncMixin[PKType, ModelType],
    PayloadMixin[ModelType],
    SerializerProtocol[ModelType],
):
    async def update_raw(
        self,
        session: AsyncSession,
        pk: PKType,
        data: PydanticModel | dict[str, Any],
        *,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> ModelType:
        payload = self._dump_payload(data, exclude_unset=True)
        payload, relation_payload = self.split_m2m_payload(payload)
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
        options: Iterable[OptionSpec[ModelType]] | None = None,
        schema: type[BaseResponseSchema] | Literal[False] | None = None,
    ) -> BaseResponseSchema | ModelType:
        entity = await self.update_raw(session, pk, data, options=options)
        return self.serialize_one(entity, schema=schema)


class UpdateByFilterServiceMixin[PKType, ModelType: GenericBaseModel](
    SessionExecutorMixin[PKType, ModelType],
    RepositoryAccessorMixin[PKType, ModelType],
    PayloadMixin[ModelType],
    SerializerProtocol[ModelType],
):
    async def update_by_raw(
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
        data: PydanticModel | dict[str, Any],
        *,
        options: Iterable[OptionSpec[ModelType]] | None = None,
    ) -> ModelType:
        payload = self._dump_payload(data, exclude_unset=True)
        query = self.repo.update_by(payload, filters=filters, options=options)
        return await self.execute_for_one(session, query)

    async def update_by(
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
        data: PydanticModel | dict[str, Any],
        *,
        options: Iterable[OptionSpec[ModelType]] | None = None,
        schema: type[BaseResponseSchema] | Literal[False] | None = None,
    ) -> BaseResponseSchema | ModelType:
        entity = await self.update_by_raw(session, filters, data, options=options)
        return self.serialize_one(entity, schema=schema)
