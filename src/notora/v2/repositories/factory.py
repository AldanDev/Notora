from typing import cast

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.base import Repository, SoftDeleteRepository
from notora.v2.repositories.config import RepoConfig

type AnyRepository[
    PKType,
    ModelType: GenericBaseModel,
] = Repository[PKType, ModelType] | SoftDeleteRepository[PKType, ModelType]

type RepositoryType[
    PKType,
    ModelType: GenericBaseModel,
] = type[Repository[PKType, ModelType]] | type[SoftDeleteRepository[PKType, ModelType]]


def build_repository[PKType, ModelType: GenericBaseModel](
    model: type[ModelType],
    *,
    config: RepoConfig[ModelType] | None = None,
    soft_delete: bool = False,
    repo_cls: RepositoryType[PKType, ModelType] | None = None,
) -> AnyRepository[PKType, ModelType]:
    """Create a repository with optional config overrides."""
    if repo_cls is None:
        repo_cls = cast(
            RepositoryType[PKType, ModelType],
            SoftDeleteRepository if soft_delete else Repository,
        )
    return repo_cls(model, config=config)
