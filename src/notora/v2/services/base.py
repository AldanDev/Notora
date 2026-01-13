from notora.persistence.models.base import GenericBaseModel
from notora.schemas.base import BaseResponseSchema

from .mixins.accessors import RepositoryProtocol, SoftDeleteRepositoryProtocol
from .mixins.create import CreateOrSkipServiceMixin, CreateServiceMixin
from .mixins.delete import DeleteServiceMixin, SoftDeleteServiceMixin
from .mixins.pagination import PaginationServiceMixin
from .mixins.retrieval import RetrievalServiceMixin
from .mixins.serializer import SerializerMixin
from .mixins.update import UpdateByFilterServiceMixin, UpdateServiceMixin
from .mixins.upsert import UpsertServiceMixin


class RepositoryService[PKType, ModelType: GenericBaseModel, ResponseSchema: BaseResponseSchema](
    SerializerMixin[ModelType, ResponseSchema],
    PaginationServiceMixin[PKType, ModelType],
    RetrievalServiceMixin[PKType, ModelType],
    CreateServiceMixin[PKType, ModelType],
    CreateOrSkipServiceMixin[PKType, ModelType],
    UpsertServiceMixin[PKType, ModelType],
    UpdateServiceMixin[PKType, ModelType],
    UpdateByFilterServiceMixin[PKType, ModelType],
    DeleteServiceMixin[PKType, ModelType],
):
    """Turnkey async service that glues repository access and serialization together."""

    def __init__(self, repo: RepositoryProtocol[PKType, ModelType]) -> None:
        self.repo = repo


class SoftDeleteRepositoryService[
    PKType,
    ModelType: GenericBaseModel,
    ResponseSchema: BaseResponseSchema,
](
    RepositoryService[PKType, ModelType, ResponseSchema],
    SoftDeleteServiceMixin[PKType, ModelType],
):
    """Repository service variant that exposes soft-delete helpers."""

    def __init__(self, repo: SoftDeleteRepositoryProtocol[PKType, ModelType]) -> None:
        super().__init__(repo)
