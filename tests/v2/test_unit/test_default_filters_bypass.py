from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from notora.v2.models.base import GenericBaseModel, SoftDeletableMixin
from notora.v2.repositories.base import Repository, SoftDeleteRepository
from notora.v2.repositories.config import RepoConfig
from notora.v2.repositories.params import PaginationParams, QueryParams


class BypassWidget(GenericBaseModel):
    name: Mapped[str] = mapped_column(String)


class SoftWidget(GenericBaseModel, SoftDeletableMixin):
    name: Mapped[str] = mapped_column(String)


def _widget_repo_with_defaults() -> Repository[object, BypassWidget]:
    config = RepoConfig[BypassWidget](
        default_filters=(BypassWidget.name == 'default',),
    )
    return Repository[object, BypassWidget](BypassWidget, config=config)


def test_list_applies_default_filters_by_default() -> None:
    repo = _widget_repo_with_defaults()
    stmt = repo.list(limit=None)
    assert "bypass_widget.name = 'default'" in str(
        stmt.compile(compile_kwargs={'literal_binds': True})
    )


def test_list_can_bypass_default_filters() -> None:
    repo = _widget_repo_with_defaults()
    stmt = repo.list(limit=None, apply_default_filters=False)
    assert "bypass_widget.name = 'default'" not in str(
        stmt.compile(compile_kwargs={'literal_binds': True})
    )


def test_count_applies_default_filters_by_default() -> None:
    repo = _widget_repo_with_defaults()
    stmt = repo.count()
    assert "bypass_widget.name = 'default'" in str(
        stmt.compile(compile_kwargs={'literal_binds': True})
    )


def test_count_can_bypass_default_filters() -> None:
    repo = _widget_repo_with_defaults()
    stmt = repo.count(apply_default_filters=False)
    assert "bypass_widget.name = 'default'" not in str(
        stmt.compile(compile_kwargs={'literal_binds': True})
    )


def test_retrieve_by_can_bypass_default_filters() -> None:
    repo = _widget_repo_with_defaults()
    stmt = repo.retrieve_by(apply_default_filters=False)
    assert "bypass_widget.name = 'default'" not in str(
        stmt.compile(compile_kwargs={'literal_binds': True})
    )


def test_list_on_soft_delete_repo_bypasses_soft_delete_filter() -> None:
    repo = SoftDeleteRepository[object, SoftWidget](SoftWidget)
    stmt = repo.list(limit=None, apply_default_filters=False)
    compiled = str(stmt.compile(compile_kwargs={'literal_binds': True}))
    assert 'deleted_at IS NULL' not in compiled


def test_list_on_soft_delete_repo_applies_soft_delete_filter_by_default() -> None:
    repo = SoftDeleteRepository[object, SoftWidget](SoftWidget)
    stmt = repo.list(limit=None)
    compiled = str(stmt.compile(compile_kwargs={'literal_binds': True}))
    assert 'deleted_at IS NULL' in compiled


def test_query_params_field_defaults_true_and_propagates() -> None:
    repo = SoftDeleteRepository[object, SoftWidget](SoftWidget)
    params = QueryParams[SoftWidget](limit=None, apply_default_filters=False)
    assert params.apply_default_filters is False
    stmt = repo.list_by_params(params)
    compiled = str(stmt.compile(compile_kwargs={'literal_binds': True}))
    assert 'deleted_at IS NULL' not in compiled


def test_pagination_params_field_defaults_true() -> None:
    params = PaginationParams[SoftWidget]()
    assert params.apply_default_filters is True
