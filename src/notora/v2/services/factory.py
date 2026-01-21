from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.base import SoftDeleteRepository
from notora.v2.repositories.config import RepoConfig
from notora.v2.repositories.factory import AnyRepository, RepositoryType, build_repository
from notora.v2.schemas.base import BaseResponseSchema
from notora.v2.services.base import RepositoryService, SoftDeleteRepositoryService
from notora.v2.services.config import ServiceConfig

type AnyService[
    PKType,
    ModelType: GenericBaseModel,
    DetailSchema: BaseResponseSchema,
    ListSchema: BaseResponseSchema = DetailSchema,
] = (
    RepositoryService[PKType, ModelType, DetailSchema, ListSchema]
    | SoftDeleteRepositoryService[PKType, ModelType, DetailSchema, ListSchema]
)

type ServiceType[
    PKType,
    ModelType: GenericBaseModel,
    DetailSchema: BaseResponseSchema,
    ListSchema: BaseResponseSchema = DetailSchema,
] = (
    type[RepositoryService[PKType, ModelType, DetailSchema, ListSchema]]
    | type[SoftDeleteRepositoryService[PKType, ModelType, DetailSchema, ListSchema]]
)


def build_service[  # noqa: C901
    PKType,
    ModelType: GenericBaseModel,
    DetailSchema: BaseResponseSchema,
    ListSchema: BaseResponseSchema = DetailSchema,
](
    model: type[ModelType],
    *,
    repo: AnyRepository[PKType, ModelType] | None = None,
    repo_config: RepoConfig[ModelType] | None = None,
    service_config: ServiceConfig[DetailSchema, ListSchema] | None = None,
    soft_delete: bool = False,
    repo_cls: RepositoryType[PKType, ModelType] | None = None,
    service_cls: ServiceType[PKType, ModelType, DetailSchema, ListSchema] | None = None,
) -> AnyService[PKType, ModelType, DetailSchema, ListSchema]:
    """Create a repository + service pair with optional config overrides."""
    if repo is None:
        repo = build_repository(
            model,
            config=repo_config,
            soft_delete=soft_delete,
            repo_cls=repo_cls,
        )
    if service_cls is None:
        if soft_delete or isinstance(repo, SoftDeleteRepository):
            if not isinstance(repo, SoftDeleteRepository):
                msg = 'Soft-delete service requires a soft-delete repository.'
                raise TypeError(msg)
            return SoftDeleteRepositoryService(repo, config=service_config)
        return RepositoryService(repo, config=service_config)

    if issubclass(service_cls, SoftDeleteRepositoryService):
        if not isinstance(repo, SoftDeleteRepository):
            msg = 'Soft-delete service requires a soft-delete repository.'
            raise TypeError(msg)
        return service_cls(repo, config=service_config)
    return service_cls(repo, config=service_config)


def build_service_for_repo[
    PKType,
    ModelType: GenericBaseModel,
    DetailSchema: BaseResponseSchema,
    ListSchema: BaseResponseSchema = DetailSchema,
](
    repo: AnyRepository[PKType, ModelType],
    *,
    service_config: ServiceConfig[DetailSchema, ListSchema] | None = None,
    service_cls: ServiceType[PKType, ModelType, DetailSchema, ListSchema] | None = None,
) -> AnyService[PKType, ModelType, DetailSchema, ListSchema]:
    """Create a service for an existing repository."""
    if service_cls is None:
        if isinstance(repo, SoftDeleteRepository):
            return SoftDeleteRepositoryService(repo, config=service_config)
        return RepositoryService(repo, config=service_config)

    if issubclass(service_cls, SoftDeleteRepositoryService):
        if not isinstance(repo, SoftDeleteRepository):
            msg = 'Soft-delete service requires a soft-delete repository.'
            raise TypeError(msg)
        return service_cls(repo, config=service_config)
    return service_cls(repo, config=service_config)
