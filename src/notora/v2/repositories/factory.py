from typing import TypeVar, cast

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.base import Repository, SoftDeleteRepository
from notora.v2.repositories.config import RepoConfig

ModelType = TypeVar('ModelType', bound=GenericBaseModel)
PKType = TypeVar('PKType')


def build_repository(
    model: type[ModelType],
    *,
    config: RepoConfig[ModelType] | None = None,
    soft_delete: bool = False,
    repo_cls: type[Repository[PKType, ModelType]]
    | type[SoftDeleteRepository[PKType, ModelType]]
    | None = None,
) -> Repository[PKType, ModelType] | SoftDeleteRepository[PKType, ModelType]:
    """Create a repository with optional config overrides."""
    if repo_cls is None:
        repo_cls = cast(
            type[Repository[PKType, ModelType]] | type[SoftDeleteRepository[PKType, ModelType]],
            SoftDeleteRepository if soft_delete else Repository,
        )
    return repo_cls(model, config=config)
