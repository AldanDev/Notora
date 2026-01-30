from sqlalchemy import String, select
from sqlalchemy.orm import Mapped, load_only, mapped_column

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.base import Repository
from notora.v2.repositories.config import RepoConfig
from notora.v2.repositories.params import QueryParams


class Widget(GenericBaseModel):
    name: Mapped[str] = mapped_column(String)


def test_list_uses_default_limit() -> None:
    repo = Repository[object, Widget](Widget)
    stmt = repo.list()
    assert ' LIMIT ' in str(stmt)


def test_list_supports_no_limit() -> None:
    repo = Repository[object, Widget](Widget)
    stmt = repo.list(limit=None)
    assert ' LIMIT ' not in str(stmt)


def test_list_applies_offset_without_limit() -> None:
    repo = Repository[object, Widget](Widget)
    stmt = repo.list(limit=None, offset=10)
    compiled = str(stmt)
    assert ' LIMIT ' not in compiled or ' LIMIT -1 ' in compiled
    assert ' OFFSET ' in compiled


def test_list_applies_options_to_base_query() -> None:
    repo = Repository[object, Widget](Widget)
    base_query = select(Widget)
    option = load_only(Widget.name)
    stmt = repo.list(base_query=base_query, options=(option,))
    assert stmt._with_options


def test_repo_config_overrides_defaults() -> None:
    default_limit = 5
    config = RepoConfig[Widget](default_limit=default_limit, pk_attribute='id')
    repo = Repository[object, Widget](Widget, config=config)
    assert repo.default_limit == default_limit
    assert repo.pk_attribute == 'id'


def test_list_by_params_respects_limit_override() -> None:
    repo = Repository[object, Widget](Widget)
    params = QueryParams[Widget](limit=None)
    stmt = repo.list_by_params(params)
    assert ' LIMIT ' not in str(stmt)


def test_list_uses_fallback_sort_attribute() -> None:
    repo = Repository[object, Widget](Widget)
    stmt = repo.list(limit=None)
    assert ' ORDER BY ' in str(stmt)
    assert 'widget.id' in str(stmt)


def test_repo_config_customizes_fallback_sort_attribute() -> None:
    config = RepoConfig[Widget](fallback_sort_attribute='name')
    repo = Repository[object, Widget](Widget, config=config)
    stmt = repo.list(limit=None)
    compiled = str(stmt)
    assert ' ORDER BY ' in compiled
    assert 'widget.name' in compiled
