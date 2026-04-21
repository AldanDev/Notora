from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, load_only, mapped_column
from sqlalchemy.sql import ColumnElement

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.base import Repository
from notora.v2.repositories.query_dsl import apply_filter_operator


class WidgetResolver(GenericBaseModel):
    name: Mapped[str] = mapped_column(String)
    count: Mapped[int] = mapped_column(Integer)


def test_resolve_filter_returns_clause_unchanged() -> None:
    repo = Repository[object, WidgetResolver](WidgetResolver)
    clause = WidgetResolver.name == 'x'
    assert repo.resolve_filter(clause) is clause


def test_resolve_filter_invokes_factory_with_model() -> None:
    repo = Repository[object, WidgetResolver](WidgetResolver)
    received: list[type[WidgetResolver]] = []

    def factory(m: type[WidgetResolver]) -> ColumnElement[bool]:
        received.append(m)
        return m.name == 'y'

    resolved = repo.resolve_filter(factory)
    assert received == [WidgetResolver]
    assert 'widget_resolver.name' in str(resolved)


def test_resolve_order_returns_clause_unchanged() -> None:
    repo = Repository[object, WidgetResolver](WidgetResolver)
    clause = WidgetResolver.name.desc()
    assert repo.resolve_order(clause) is clause


def test_resolve_order_invokes_factory() -> None:
    repo = Repository[object, WidgetResolver](WidgetResolver)
    resolved = repo.resolve_order(lambda m: m.name.asc())
    assert 'widget_resolver.name' in str(resolved)


def test_resolve_option_returns_option_unchanged() -> None:
    repo = Repository[object, WidgetResolver](WidgetResolver)
    option = load_only(WidgetResolver.name)
    assert repo.resolve_option(option) is option


def test_apply_filter_operator_is_public() -> None:
    clause = apply_filter_operator(WidgetResolver.count, 'gte', 10)
    rendered = str(clause.compile(compile_kwargs={'literal_binds': True}))
    assert 'widget_resolver.count >= 10' in rendered
