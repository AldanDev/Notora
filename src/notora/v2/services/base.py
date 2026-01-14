from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.base import RepositoryProtocol, SoftDeleteRepositoryProtocol
from notora.v2.schemas.base import BaseResponseSchema
from notora.v2.services.config import ServiceConfig
from notora.v2.services.mixins.create import CreateOrSkipServiceMixin, CreateServiceMixin
from notora.v2.services.mixins.delete import DeleteServiceMixin, SoftDeleteServiceMixin
from notora.v2.services.mixins.pagination import PaginationServiceMixin
from notora.v2.services.mixins.retrieval import RetrievalServiceMixin
from notora.v2.services.mixins.serializer import SerializerMixin
from notora.v2.services.mixins.update import UpdateByFilterServiceMixin, UpdateServiceMixin
from notora.v2.services.mixins.upsert import UpsertServiceMixin


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

    def __init__(
        self,
        repo: RepositoryProtocol[PKType, ModelType],
        *,
        config: ServiceConfig[ResponseSchema] | None = None,
    ) -> None:
        self.repo = repo
        if config is None:
            return
        if config.detail_schema is not None:
            self.detail_schema = config.detail_schema
        if config.list_schema is not None:
            self.list_schema = config.list_schema


class SoftDeleteRepositoryService[
    PKType,
    ModelType: GenericBaseModel,
    ResponseSchema: BaseResponseSchema,
](
    RepositoryService[PKType, ModelType, ResponseSchema],
    SoftDeleteServiceMixin[PKType, ModelType],
):
    """Repository service variant that exposes soft-delete helpers."""

    def __init__(
        self,
        repo: SoftDeleteRepositoryProtocol[PKType, ModelType],
        *,
        config: ServiceConfig[ResponseSchema] | None = None,
    ) -> None:
        super().__init__(repo, config=config)
