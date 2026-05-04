"""Tests for build_repository, build_service, and build_service_for_repo factories."""

from typing import Any

import pytest
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from notora.v2.models.base import GenericBaseModel, SoftDeletableModel
from notora.v2.repositories.base import Repository, SoftDeleteRepository
from notora.v2.repositories.config import RepoConfig
from notora.v2.repositories.factory import AnyRepository, build_repository
from notora.v2.schemas.base import BaseResponseSchema
from notora.v2.services.base import RepositoryService, SoftDeleteRepositoryService
from notora.v2.services.factory import AnyService, build_service, build_service_for_repo

_DEFAULT_LIMIT = 7
_REPO_CONFIG_LIMIT = 3


class _Widget(GenericBaseModel):
    name: Mapped[str] = mapped_column(String)


class _SoftWidget(SoftDeletableModel):
    name: Mapped[str] = mapped_column(String)


class _WidgetSchema(BaseResponseSchema):
    pass


def test_build_repository_returns_standard_repo_by_default() -> None:
    repo: AnyRepository[object, _Widget] = build_repository(_Widget)
    assert isinstance(repo, Repository)
    assert not isinstance(repo, SoftDeleteRepository)


def test_build_repository_soft_delete_flag_returns_soft_delete_repo() -> None:
    repo: AnyRepository[object, _SoftWidget] = build_repository(_SoftWidget, soft_delete=True)
    assert isinstance(repo, SoftDeleteRepository)


def test_build_repository_config_is_applied() -> None:
    config = RepoConfig[_Widget](default_limit=_DEFAULT_LIMIT)
    repo: AnyRepository[object, _Widget] = build_repository(_Widget, config=config)
    assert repo.default_limit == _DEFAULT_LIMIT


def test_build_repository_custom_repo_class_used() -> None:
    class _CustomRepo(Repository[object, _Widget]):
        pass

    repo: AnyRepository[object, _Widget] = build_repository(_Widget, repo_cls=_CustomRepo)
    assert isinstance(repo, _CustomRepo)


def test_build_repository_model_attribute_set() -> None:
    repo: AnyRepository[object, _Widget] = build_repository(_Widget)
    assert repo.model is _Widget


def test_build_service_returns_repository_service_by_default() -> None:
    svc: AnyService[object, _Widget, Any, Any] = build_service(_Widget)
    assert isinstance(svc, RepositoryService)


def test_build_service_soft_delete_flag_returns_soft_delete_service() -> None:
    svc: AnyService[object, _SoftWidget, Any, Any] = build_service(_SoftWidget, soft_delete=True)
    assert isinstance(svc, SoftDeleteRepositoryService)


def test_build_service_custom_repo_passed_directly() -> None:
    repo = Repository[object, _Widget](_Widget)
    svc: AnyService[object, _Widget, Any, Any] = build_service(_Widget, repo=repo)
    assert isinstance(svc, RepositoryService)
    assert svc.repo is repo


def test_build_service_soft_delete_repo_infers_soft_delete_service() -> None:
    repo = SoftDeleteRepository[object, _SoftWidget](_SoftWidget)
    svc: AnyService[object, _SoftWidget, Any, Any] = build_service(_SoftWidget, repo=repo)
    assert isinstance(svc, SoftDeleteRepositoryService)


def test_build_service_soft_delete_service_class_with_non_soft_delete_repo_raises() -> None:
    repo = Repository[object, _Widget](_Widget)
    with pytest.raises(TypeError, match='Soft-delete service requires'):
        build_service(_Widget, repo=repo, service_cls=SoftDeleteRepositoryService)


def test_build_service_soft_delete_flag_with_explicit_service_class() -> None:
    svc: AnyService[object, _SoftWidget, Any, Any] = build_service(
        _SoftWidget,
        soft_delete=True,
        service_cls=SoftDeleteRepositoryService,
    )
    assert isinstance(svc, SoftDeleteRepositoryService)


def test_build_service_repo_config_applied() -> None:
    repo_config = RepoConfig[_Widget](default_limit=_REPO_CONFIG_LIMIT)
    svc: AnyService[object, _Widget, Any, Any] = build_service(_Widget, repo_config=repo_config)
    assert svc.repo.default_limit == _REPO_CONFIG_LIMIT


def test_build_service_soft_delete_repo_with_soft_delete_true() -> None:
    repo = SoftDeleteRepository[object, _SoftWidget](_SoftWidget)
    svc: AnyService[object, _SoftWidget, Any, Any] = build_service(
        _SoftWidget, soft_delete=True, repo=repo
    )
    assert isinstance(svc, SoftDeleteRepositoryService)


def test_build_service_for_repo_standard_repo_returns_repository_service() -> None:
    repo = Repository[object, _Widget](_Widget)
    svc: AnyService[object, _Widget, Any, Any] = build_service_for_repo(repo)
    assert isinstance(svc, RepositoryService)


def test_build_service_for_repo_soft_delete_repo_returns_soft_delete_service() -> None:
    repo = SoftDeleteRepository[object, _SoftWidget](_SoftWidget)
    svc: AnyService[object, _SoftWidget, Any, Any] = build_service_for_repo(repo)
    assert isinstance(svc, SoftDeleteRepositoryService)


def test_build_service_for_repo_custom_service_class_used() -> None:
    class _CustomService(RepositoryService[object, _Widget, _WidgetSchema]):
        pass

    repo = Repository[object, _Widget](_Widget)
    svc: AnyService[object, _Widget, Any, Any] = build_service_for_repo(
        repo, service_cls=_CustomService
    )
    assert isinstance(svc, _CustomService)


def test_build_service_for_repo_soft_delete_service_cls_with_non_soft_delete_repo_raises() -> None:
    repo = Repository[object, _Widget](_Widget)
    with pytest.raises(TypeError, match='Soft-delete service requires'):
        build_service_for_repo(repo, service_cls=SoftDeleteRepositoryService)


def test_build_service_for_repo_repo_is_wired_to_service() -> None:
    repo = Repository[object, _Widget](_Widget)
    svc: AnyService[object, _Widget, Any, Any] = build_service_for_repo(repo)
    assert svc.repo is repo
