from collections.abc import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.base import SoftDeleteRepositoryProtocol
from notora.v2.repositories.types import FilterSpec
from notora.v2.services.mixins.accessors import RepositoryAccessorMixin
from notora.v2.services.mixins.executor import SessionExecutorMixin


class DeleteServiceMixin[PKType, ModelType: GenericBaseModel](
    SessionExecutorMixin[PKType, ModelType],
    RepositoryAccessorMixin[PKType, ModelType],
):
    async def delete(self, session: AsyncSession, pk: PKType) -> None:
        await self.execute(session, self.repo.delete(pk))

    async def delete_by(
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
    ) -> None:
        await self.execute(session, self.repo.delete_by(filters=filters))


class SoftDeleteServiceMixin[PKType, ModelType: GenericBaseModel](
    DeleteServiceMixin[PKType, ModelType],
):
    repo: SoftDeleteRepositoryProtocol[PKType, ModelType]

    async def soft_delete(self, session: AsyncSession, pk: PKType) -> None:
        await self.execute(session, self.repo.soft_delete(pk))

    async def soft_delete_by(
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
    ) -> None:
        await self.execute(session, self.repo.soft_delete_by(filters=filters))
