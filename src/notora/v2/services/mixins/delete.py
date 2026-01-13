from collections.abc import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from notora.v2.models.base import GenericBaseModel

from ...repositories.base import SoftDeleteRepositoryProtocol
from ...repositories.types import FilterSpec
from .accessors import RepositoryAccessorMixin
from .executor import SessionExecutorMixin


class DeleteServiceMixin[PKType, ModelType: GenericBaseModel](
    SessionExecutorMixin[PKType, ModelType],
    RepositoryAccessorMixin[PKType, ModelType],
):
    async def delete(self, session: AsyncSession, pk: PKType) -> None:
        await session.execute(self.repo.delete(pk))

    async def delete_by(
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
    ) -> None:
        await session.execute(self.repo.delete_by(filters=filters))


class SoftDeleteServiceMixin[PKType, ModelType: GenericBaseModel](
    DeleteServiceMixin[PKType, ModelType],
):
    repo: SoftDeleteRepositoryProtocol[PKType, ModelType]

    async def soft_delete(self, session: AsyncSession, pk: PKType) -> None:
        await session.execute(self.repo.soft_delete(pk))

    async def soft_delete_by(
        self,
        session: AsyncSession,
        filters: Iterable[FilterSpec[ModelType]],
    ) -> None:
        await session.execute(self.repo.soft_delete_by(filters=filters))
