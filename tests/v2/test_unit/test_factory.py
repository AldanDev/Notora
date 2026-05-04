"""Tests for build_repository, build_service, and build_service_for_repo factories."""

import pytest
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.base import Repository, SoftDeleteRepository
from notora.v2.repositories.config import RepoConfig
from notora.v2.repositories.factory import build_repository
from notora.v2.schemas.base import BaseResponseSchema
from notora.v2.services.base import RepositoryService, SoftDeleteRepositoryService
from notora.v2.services.factory import build_service, build_service_for_repo


class _Widget(GenericBaseModel):
    name: Mapped[str] = mapped_column(String)


class _WidgetSchema(BaseResponseSchema):
    pass


class TestBuildRepository:
    def test_returns_standard_repo_by_default(self) -> None:
        repo = build_repository(_Widget)
        assert isinstance(repo, Repository)
        assert not isinstance(repo, SoftDeleteRepository)

    def test_soft_delete_flag_returns_soft_delete_repo(self) -> None:
        repo = build_repository(_Widget, soft_delete=True)
        assert isinstance(repo, SoftDeleteRepository)

    def test_config_is_applied(self) -> None:
        config = RepoConfig[_Widget](default_limit=7)
        repo = build_repository(_Widget, config=config)
        assert repo.default_limit == 7

    def test_custom_repo_class_used(self) -> None:
        class _CustomRepo(Repository[object, _Widget]):
            pass

        repo = build_repository(_Widget, repo_cls=_CustomRepo)
        assert isinstance(repo, _CustomRepo)

    def test_model_attribute_set(self) -> None:
        repo = build_repository(_Widget)
        assert repo.model is _Widget


class TestBuildService:
    def test_returns_repository_service_by_default(self) -> None:
        svc = build_service(_Widget)
        assert isinstance(svc, RepositoryService)

    def test_soft_delete_flag_returns_soft_delete_service(self) -> None:
        svc = build_service(_Widget, soft_delete=True)
        assert isinstance(svc, SoftDeleteRepositoryService)

    def test_custom_repo_passed_directly(self) -> None:
        repo = Repository[object, _Widget](_Widget)
        svc = build_service(_Widget, repo=repo)
        assert isinstance(svc, RepositoryService)
        assert svc.repo is repo

    def test_soft_delete_repo_infers_soft_delete_service(self) -> None:
        repo = SoftDeleteRepository[object, _Widget](_Widget)
        svc = build_service(_Widget, repo=repo)
        assert isinstance(svc, SoftDeleteRepositoryService)

    def test_soft_delete_service_class_with_non_soft_delete_repo_raises(self) -> None:
        repo = Repository[object, _Widget](_Widget)
        with pytest.raises(TypeError, match='Soft-delete service requires'):
            build_service(_Widget, repo=repo, service_cls=SoftDeleteRepositoryService)

    def test_soft_delete_flag_with_standard_service_class_used(self) -> None:
        svc = build_service(
            _Widget,
            soft_delete=True,
            service_cls=SoftDeleteRepositoryService,
        )
        assert isinstance(svc, SoftDeleteRepositoryService)

    def test_repo_config_applied(self) -> None:
        repo_config = RepoConfig[_Widget](default_limit=3)
        svc = build_service(_Widget, repo_config=repo_config)
        assert svc.repo.default_limit == 3

    def test_soft_delete_true_without_matching_service_cls_raises(self) -> None:
        """Passing a plain Repository as repo + soft_delete=True internally should be fine
        only if the repo is SoftDeleteRepository.  When soft_delete=True is inferred
        from the build_repository call, we get a SoftDeleteRepository automatically."""
        repo = SoftDeleteRepository[object, _Widget](_Widget)
        svc = build_service(_Widget, soft_delete=True, repo=repo)
        assert isinstance(svc, SoftDeleteRepositoryService)


class TestBuildServiceForRepo:
    def test_standard_repo_returns_repository_service(self) -> None:
        repo = Repository[object, _Widget](_Widget)
        svc = build_service_for_repo(repo)
        assert isinstance(svc, RepositoryService)

    def test_soft_delete_repo_returns_soft_delete_service(self) -> None:
        repo = SoftDeleteRepository[object, _Widget](_Widget)
        svc = build_service_for_repo(repo)
        assert isinstance(svc, SoftDeleteRepositoryService)

    def test_custom_service_class_used(self) -> None:
        class _CustomService(RepositoryService[object, _Widget, _WidgetSchema]):
            pass

        repo = Repository[object, _Widget](_Widget)
        svc = build_service_for_repo(repo, service_cls=_CustomService)
        assert isinstance(svc, _CustomService)

    def test_soft_delete_service_cls_with_non_soft_delete_repo_raises(self) -> None:
        repo = Repository[object, _Widget](_Widget)
        with pytest.raises(TypeError, match='Soft-delete service requires'):
            build_service_for_repo(repo, service_cls=SoftDeleteRepositoryService)

    def test_repo_is_wired_to_service(self) -> None:
        repo = Repository[object, _Widget](_Widget)
        svc = build_service_for_repo(repo)
        assert svc.repo is repo
