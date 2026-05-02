from typing import Annotated, Any, ClassVar, Literal, cast
from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import ColumnElement, or_

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.types import FilterSpec, OrderSpec
from notora.v2.schemas.query import (
    Filter,
    PydanticFilterField,
    PydanticFiltersSchema,
    PydanticOrderBySchema,
    PydanticSortField,
    _extract_annotated_filters,
)


class Thing(GenericBaseModel):
    name: Mapped[str] = mapped_column(String)
    age: Mapped[int] = mapped_column(Integer)
    owner_id: Mapped[UUID] = mapped_column(PGUUID)
    is_active: Mapped[bool] = mapped_column(Boolean)


class ThingFilters(PydanticFiltersSchema[Thing]):
    name: str | None = None
    age_gte: int | None = None
    owner_id: UUID | None = None
    is_active: bool | None = None
    q: str | None = None

    filter_fields: ClassVar[dict[str, PydanticFilterField[Any]]] = {
        'name': PydanticFilterField(resolver=Thing.name),
        'age_gte': PydanticFilterField(resolver=Thing.age, operator='gte'),
        'owner_id': PydanticFilterField(resolver=Thing.owner_id),
        'is_active': PydanticFilterField(resolver=Thing.is_active),
        'q': PydanticFilterField(
            predicate=lambda m, op, v: or_(
                m.name.ilike(f'%{v}%'),
                m.owner_id.cast(String).ilike(f'%{v}%'),
            ),
        ),
    }


class ThingOrdering(PydanticOrderBySchema[Thing]):
    order_by: Literal['name', 'age'] | None = None
    direction: Literal['asc', 'desc'] = 'asc'

    sort_fields: ClassVar[dict[str, PydanticSortField[Any]]] = {
        'name': PydanticSortField(resolver=Thing.name),
        'age': PydanticSortField(resolver=Thing.age),
    }


def _render(spec: FilterSpec[Any] | OrderSpec[Any]) -> str:
    assert not callable(spec)
    clause = cast(ColumnElement[Any], spec)
    return str(
        clause.compile(
            dialect=postgresql.dialect(),  # type: ignore[no-untyped-call]
            compile_kwargs={'literal_binds': True},
        ),
    )


def test_unset_fields_produce_no_specs() -> None:
    filters = ThingFilters()
    assert filters.build_filter_specs(Thing) == []


def test_none_values_are_excluded() -> None:
    filters = ThingFilters(name=None, age_gte=None)
    assert filters.build_filter_specs(Thing) == []


def test_equality_field_produces_eq_clause() -> None:
    filters = ThingFilters(name='foo')
    specs = filters.build_filter_specs(Thing)
    assert len(specs) == 1
    assert "thing.name = 'foo'" in _render(specs[0])


def test_operator_override_gte() -> None:
    expected_age = 18
    filters = ThingFilters(age_gte=expected_age)
    specs = filters.build_filter_specs(Thing)
    assert len(specs) == 1
    assert f'thing.age >= {expected_age}' in _render(specs[0])


def test_uuid_field_produces_eq_clause() -> None:
    target = uuid4()
    filters = ThingFilters(owner_id=target)
    specs = filters.build_filter_specs(Thing)
    assert len(specs) == 1
    assert str(target) in _render(specs[0])


def test_bool_false_still_produces_clause() -> None:
    filters = ThingFilters(is_active=False)
    specs = filters.build_filter_specs(Thing)
    assert len(specs) == 1
    assert 'thing.is_active = false' in _render(specs[0])


def test_predicate_based_field() -> None:
    filters = ThingFilters(q='sea')
    specs = filters.build_filter_specs(Thing)
    assert len(specs) == 1
    rendered = _render(specs[0])
    assert 'sea' in rendered
    assert 'thing.name ILIKE' in rendered


def test_field_absent_from_allowlist_is_skipped() -> None:
    class ExtraFilters(PydanticFiltersSchema[Thing]):
        name: str | None = None
        untracked: str | None = None
        filter_fields: ClassVar[dict[str, PydanticFilterField[Any]]] = {
            'name': PydanticFilterField(resolver=Thing.name),
        }

    f = ExtraFilters(name='x', untracked='y')
    specs = f.build_filter_specs(Thing)
    assert len(specs) == 1
    assert "thing.name = 'x'" in _render(specs[0])


def test_order_by_none_produces_no_ordering() -> None:
    order = ThingOrdering()
    assert order.build_ordering(Thing) == []


def test_order_by_ascending() -> None:
    order = ThingOrdering(order_by='name', direction='asc')
    specs = order.build_ordering(Thing)
    assert len(specs) == 1
    assert 'thing.name ASC' in _render(specs[0])


def test_order_by_descending() -> None:
    order = ThingOrdering(order_by='age', direction='desc')
    specs = order.build_ordering(Thing)
    assert len(specs) == 1
    assert 'thing.age DESC' in _render(specs[0])


def test_order_by_unknown_field_raises() -> None:
    class BrokenOrder(PydanticOrderBySchema[Thing]):
        order_by: str | None = None
        direction: Literal['asc', 'desc'] = 'asc'
        sort_fields: ClassVar[dict[str, PydanticSortField[Any]]] = {}

    order = BrokenOrder(order_by='name')
    with pytest.raises(ValueError, match='Unsupported sort field'):
        order.build_ordering(Thing)


def test_filter_field_without_resolver_or_predicate_raises() -> None:
    class BrokenFilters(PydanticFiltersSchema[Thing]):
        name: str | None = None
        filter_fields: ClassVar[dict[str, PydanticFilterField[Any]]] = {
            'name': PydanticFilterField(),
        }

    f = BrokenFilters(name='x')
    with pytest.raises(ValueError, match='resolver or predicate'):
        f.build_filter_specs(Thing)


def test_resolver_can_be_callable() -> None:
    class CallableResolverFilters(PydanticFiltersSchema[Thing]):
        name: str | None = None
        filter_fields: ClassVar[dict[str, PydanticFilterField[Any]]] = {
            'name': PydanticFilterField(resolver=lambda m: m.name),
        }

    f = CallableResolverFilters(name='y')
    specs = f.build_filter_specs(Thing)
    assert "thing.name = 'y'" in _render(specs[0])


def test_filter_constructs_with_resolver_only() -> None:
    f = Filter(resolver=Thing.name)
    assert f.resolver is Thing.name
    assert f.predicate is None
    assert f.operator == 'eq'


def test_filter_constructs_with_predicate_only() -> None:
    def pred(model: type[Thing], _op: str, value: str) -> ColumnElement[bool]:  # noqa: ARG001
        return model.name == value

    f = Filter(predicate=pred)
    assert f.predicate is pred
    assert f.resolver is None
    assert f.operator == 'eq'


def test_filter_operator_override() -> None:
    f = Filter(resolver=Thing.age, operator='gte')
    assert f.operator == 'gte'


def test_filter_without_resolver_or_predicate_raises() -> None:
    with pytest.raises(TypeError, match='exactly one of resolver= or predicate='):
        Filter()


def test_filter_with_both_resolver_and_predicate_raises() -> None:
    def pred(model: type[Thing], _op: str, value: str) -> ColumnElement[bool]:  # noqa: ARG001
        return model.name == value

    with pytest.raises(TypeError, match='exactly one of resolver= or predicate='):
        Filter(resolver=Thing.name, predicate=pred)


def test_extract_annotated_filters_returns_empty_for_no_metadata() -> None:
    class NoFilters(BaseModel):
        name: str | None = None

    assert _extract_annotated_filters(NoFilters) == {}


def test_extract_annotated_filters_returns_one_per_field() -> None:
    class WithFilter(BaseModel):
        name: Annotated[str | None, Filter(resolver=Thing.name)] = None

    out = _extract_annotated_filters(WithFilter)
    assert set(out) == {'name'}
    assert isinstance(out['name'], Filter)
    assert out['name'].resolver is Thing.name


def test_extract_annotated_filters_skips_non_filter_metadata() -> None:
    class Mixed(BaseModel):
        name: Annotated[str | None, Filter(resolver=Thing.name)] = Field(default=None, description='X')
        plain: str | None = None

    out = _extract_annotated_filters(Mixed)
    assert set(out) == {'name'}


def test_extract_annotated_filters_raises_on_multiple_filters_in_one_field() -> None:
    with pytest.raises(TypeError, match='multiple Filter'):
        class Conflict(BaseModel):
            name: Annotated[
                str | None,
                Filter(resolver=Thing.name),
                Filter(predicate=lambda m, _op, v: m.name == v),
            ] = None

        _extract_annotated_filters(Conflict)


def test_pydantic_init_subclass_caches_annotated_filters() -> None:
    class FooFilters(PydanticFiltersSchema[Thing]):
        name: Annotated[str | None, Filter(resolver=Thing.name)] = None
        age: Annotated[int | None, Filter(resolver=Thing.age, operator='gte')] = None

    assert set(FooFilters._annotated_filter_fields) == {'name', 'age'}
    assert FooFilters._annotated_filter_fields['age'].operator == 'gte'


def test_pydantic_init_subclass_empty_cache_when_no_annotated_filters() -> None:
    class LegacyFilters(PydanticFiltersSchema[Thing]):
        name: str | None = None
        filter_fields: ClassVar[dict[str, PydanticFilterField[Any]]] = {
            'name': PydanticFilterField(resolver=Thing.name),
        }

    assert LegacyFilters._annotated_filter_fields == {}


def test_mixing_legacy_dict_and_annotated_filter_raises() -> None:
    with pytest.raises(TypeError, match='mixes legacy `filter_fields` ClassVar'):
        class Mixed(PydanticFiltersSchema[Thing]):
            name: Annotated[str | None, Filter(resolver=Thing.name)] = None
            age: int | None = None
            filter_fields: ClassVar[dict[str, PydanticFilterField[Any]]] = {
                'age': PydanticFilterField(resolver=Thing.age),
            }


def test_mixing_via_inheritance_raises() -> None:
    class LegacyParent(PydanticFiltersSchema[Thing]):
        name: str | None = None
        filter_fields: ClassVar[dict[str, PydanticFilterField[Any]]] = {
            'name': PydanticFilterField(resolver=Thing.name),
        }

    with pytest.raises(TypeError, match='mixes legacy `filter_fields` ClassVar'):
        class AnnotatedChild(LegacyParent):
            age: Annotated[int | None, Filter(resolver=Thing.age)] = None


def test_pure_annotated_inheritance_works() -> None:
    class AnnotatedParent(PydanticFiltersSchema[Thing]):
        name: Annotated[str | None, Filter(resolver=Thing.name)] = None

    class AnnotatedChild(AnnotatedParent):
        age: Annotated[int | None, Filter(resolver=Thing.age)] = None

    assert set(AnnotatedChild._annotated_filter_fields) == {'name', 'age'}


def test_annotated_schema_builds_filter_specs() -> None:
    class FooFilters(PydanticFiltersSchema[Thing]):
        name: Annotated[str | None, Filter(resolver=Thing.name)] = None
        age_gte: Annotated[int | None, Filter(resolver=Thing.age, operator='gte')] = None

    expected_age = 18
    filters = FooFilters(name='alice', age_gte=expected_age)
    specs = filters.build_filter_specs(Thing)
    rendered = sorted(_render(s) for s in specs)
    assert any("thing.name = 'alice'" in r for r in rendered)
    assert any(f'thing.age >= {expected_age}' in r for r in rendered)
    assert len(specs) == 2
