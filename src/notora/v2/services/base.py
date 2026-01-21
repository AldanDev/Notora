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


class RepositoryService[
    PKType,
    ModelType: GenericBaseModel,
    DetailSchema: BaseResponseSchema,
    ListSchema: BaseResponseSchema = DetailSchema,
](
    SerializerMixin[ModelType, DetailSchema, ListSchema],
    PaginationServiceMixin[PKType, ModelType, DetailSchema, ListSchema],
    RetrievalServiceMixin[PKType, ModelType, DetailSchema, ListSchema],
    CreateServiceMixin[PKType, ModelType, DetailSchema, ListSchema],
    CreateOrSkipServiceMixin[PKType, ModelType, DetailSchema, ListSchema],
    UpsertServiceMixin[PKType, ModelType, DetailSchema, ListSchema],
    UpdateServiceMixin[PKType, ModelType, DetailSchema, ListSchema],
    UpdateByFilterServiceMixin[PKType, ModelType, DetailSchema, ListSchema],
    DeleteServiceMixin[PKType, ModelType],
):
    """Turnkey async service that glues repository access and serialization together."""

    def __init__(
        self,
        repo: RepositoryProtocol[PKType, ModelType],
        *,
        config: ServiceConfig[DetailSchema, ListSchema] | None = None,
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
    DetailSchema: BaseResponseSchema,
    ListSchema: BaseResponseSchema = DetailSchema,
](
    RepositoryService[PKType, ModelType, DetailSchema, ListSchema],
    SoftDeleteServiceMixin[PKType, ModelType],
):
    """Repository service variant that exposes soft-delete helpers."""

    def __init__(
        self,
        repo: SoftDeleteRepositoryProtocol[PKType, ModelType],
        *,
        config: ServiceConfig[DetailSchema, ListSchema] | None = None,
    ) -> None:
        super().__init__(repo, config=config)


type RepositoryServiceD[
    PKType,
    ModelType: GenericBaseModel,
    DetailSchema: BaseResponseSchema,
] = RepositoryService[PKType, ModelType, DetailSchema, DetailSchema]


type SoftDeleteRepositoryServiceD[
    PKType,
    ModelType: GenericBaseModel,
    DetailSchema: BaseResponseSchema,
] = SoftDeleteRepositoryService[PKType, ModelType, DetailSchema, DetailSchema]
