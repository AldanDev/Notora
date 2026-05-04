"""Tests for query_dsl token parsers, filter/sort clause builders, and build_query_params."""

from typing import Any, cast

import pytest
from pydantic import ValidationError
from sqlalchemy import Integer, String, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import ColumnElement

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.query_dsl import (
    FilterField,
    FilterToken,
    QueryInput,
    SortField,
    SortToken,
    apply_filter_operator,
    build_filter_clauses,
    build_query_params,
    build_sort_clauses,
    parse_filter_token,
    parse_sort_token,
    resolve_to_column,
)

_MULTI_CLAUSE_COUNT = 2
_POSITIVE_OFFSET = 100
_POSITIVE_LIMIT = 50
_LIMIT_SMALL = 5
_OFFSET_SMALL = 10

def _render(clause: ColumnElement) -> str:  # type: ignore[type-arg]
    return str(
        clause.compile(
            dialect=postgresql.dialect(),  # type: ignore[no-untyped-call]
            compile_kwargs={'literal_binds': True},
        )
    )

class SampleModel(GenericBaseModel):
    name: Mapped[str] = mapped_column(String)
    score: Mapped[int] = mapped_column(Integer)

def test_parse_filter_token_parses_field_op_value() -> None:
    token = parse_filter_token('name:eq:alice')
    assert token.field == 'name'
    assert token.operator == 'eq'
    assert token.raw_value == 'alice'

def test_parse_filter_token_parses_operator_only_for_isnull() -> None:
    token = parse_filter_token('name:isnull')
    assert token.field == 'name'
    assert token.operator == 'isnull'
    assert token.raw_value is None

def test_parse_filter_token_raises_for_missing_colon() -> None:
    with pytest.raises(ValueError, match='"field:op:value"'):
        parse_filter_token('nocolon')

def test_parse_filter_token_raises_for_empty_field_name() -> None:
    with pytest.raises(ValueError, match='field name cannot be empty'):
        parse_filter_token(':eq:value')

def test_parse_filter_token_raises_for_unsupported_operator() -> None:
    with pytest.raises(ValueError, match='Unsupported filter operator'):
        parse_filter_token('name:contains:hello')

def test_parse_filter_token_value_with_colons_preserved() -> None:
    token = parse_filter_token('name:eq:a:b:c')
    assert token.raw_value == 'a:b:c'

def test_parse_filter_token_whitespace_stripped_from_field_and_op() -> None:
    token = parse_filter_token(' name : eq : alice ')
    assert token.field == 'name'
    assert token.operator == 'eq'

def test_parse_filter_token_whitespace_only_value_becomes_none() -> None:
    token = parse_filter_token('name:eq:   ')
    assert token.raw_value is None

def test_parse_filter_token_all_operators_accepted() -> None:
    valid_ops = ('eq', 'ne', 'lt', 'lte', 'gt', 'gte', 'in', 'ilike', 'isnull')
    for op in valid_ops:
        token = parse_filter_token(f'name:{op}:x')
        assert token.operator == op

def test_parse_filter_token_isnull_with_false_value() -> None:
    token = parse_filter_token('name:isnull:false')
    assert token.raw_value == 'false'

def test_parse_filter_token_in_with_comma_separated_value() -> None:
    token = parse_filter_token('score:in:1,2,3')
    assert token.raw_value == '1,2,3'

def test_parse_sort_token_plain_field_is_ascending() -> None:
    token = parse_sort_token('name')
    assert token.field == 'name'
    assert token.direction == 'asc'

def test_parse_sort_token_plus_prefix_is_ascending() -> None:
    token = parse_sort_token('+name')
    assert token.field == 'name'
    assert token.direction == 'asc'

def test_parse_sort_token_minus_prefix_is_descending() -> None:
    token = parse_sort_token('-score')
    assert token.field == 'score'
    assert token.direction == 'desc'

def test_parse_sort_token_empty_string_raises() -> None:
    with pytest.raises(ValueError, match='cannot be empty'):
        parse_sort_token('')

def test_parse_sort_token_only_minus_raises() -> None:
    with pytest.raises(ValueError, match='cannot be empty'):
        parse_sort_token('-')

def test_parse_sort_token_only_plus_raises() -> None:
    with pytest.raises(ValueError, match='cannot be empty'):
        parse_sort_token('+')

def test_parse_sort_token_whitespace_stripped() -> None:
    token = parse_sort_token('  name  ')
    assert token.field == 'name'

def test_parse_sort_token_returns_sort_token_dataclass() -> None:
    token = parse_sort_token('name')
    assert isinstance(token, SortToken)

def test_apply_filter_operator_eq() -> None:
    clause = apply_filter_operator(SampleModel.name, 'eq', 'alice')
    assert "sample_model.name = 'alice'" in _render(clause)

def test_apply_filter_operator_ne() -> None:
    clause = apply_filter_operator(SampleModel.name, 'ne', 'alice')
    rendered = _render(clause)
    assert 'sample_model.name' in rendered
    assert '!=' in rendered or '<>' in rendered

def test_apply_filter_operator_lt() -> None:
    clause = apply_filter_operator(SampleModel.score, 'lt', 5)
    assert 'sample_model.score < 5' in _render(clause)

def test_apply_filter_operator_lte() -> None:
    clause = apply_filter_operator(SampleModel.score, 'lte', 5)
    assert 'sample_model.score <= 5' in _render(clause)

def test_apply_filter_operator_gt() -> None:
    clause = apply_filter_operator(SampleModel.score, 'gt', 5)
    assert 'sample_model.score > 5' in _render(clause)

def test_apply_filter_operator_gte() -> None:
    clause = apply_filter_operator(SampleModel.score, 'gte', 5)
    assert 'sample_model.score >= 5' in _render(clause)

def test_apply_filter_operator_in() -> None:
    clause = apply_filter_operator(SampleModel.score, 'in', [1, 2, 3])
    assert 'IN' in _render(clause)

def test_apply_filter_operator_ilike() -> None:
    clause = apply_filter_operator(SampleModel.name, 'ilike', '%alice%')
    assert 'ILIKE' in _render(clause)

def test_apply_filter_operator_isnull_true() -> None:
    clause = apply_filter_operator(SampleModel.name, 'isnull', value=True)
    assert 'IS NULL' in _render(clause)

def test_apply_filter_operator_isnull_false() -> None:
    clause = apply_filter_operator(SampleModel.name, 'isnull', value=False)
    assert 'IS NOT NULL' in _render(clause)

def test_apply_filter_operator_unsupported_operator_raises() -> None:
    with pytest.raises(ValueError, match='Unsupported filter operator'):
        apply_filter_operator(SampleModel.name, 'contains', 'x')  # type: ignore[arg-type]

def test_resolve_to_column_direct_column_returned_unchanged() -> None:
    col = resolve_to_column(SampleModel.name, SampleModel)
    assert 'sample_model.name' in _render(cast(ColumnElement[Any], col))

def test_resolve_to_column_callable_resolver_called_with_model() -> None:
    col = resolve_to_column(lambda m: m.score, SampleModel)
    assert 'sample_model.score' in _render(cast(ColumnElement[Any], col))

def test_build_filter_clauses_single_eq_clause() -> None:
    tokens = [FilterToken(field='name', operator='eq', raw_value='alice')]
    fields: dict[str, FilterField[SampleModel]] = {'name': FilterField(resolver=SampleModel.name, value_type=str)}
    clauses = build_filter_clauses(tokens, model=SampleModel, fields=fields)
    assert len(clauses) == 1
    assert "sample_model.name = 'alice'" in _render(clauses[0])

def test_build_filter_clauses_unknown_field_raises() -> None:
    tokens = [FilterToken(field='unknown', operator='eq', raw_value='x')]
    with pytest.raises(ValueError, match='Unsupported filter field'):
        build_filter_clauses(tokens, model=SampleModel, fields={})

def test_build_filter_clauses_disallowed_operator_raises() -> None:
    tokens = [FilterToken(field='name', operator='gt', raw_value='5')]
    fields: dict[str, FilterField[SampleModel]] = {'name': FilterField(resolver=SampleModel.name, operators=frozenset({'eq'}))}
    with pytest.raises(ValueError, match='Operator'):
        build_filter_clauses(tokens, model=SampleModel, fields=fields)

def test_build_filter_clauses_predicate_field() -> None:
    def pred(model: type[SampleModel], _op: str, value: str) -> ColumnElement[bool]:
        return model.name.ilike(f'%{value}%')

    tokens = [FilterToken(field='q', operator='eq', raw_value='alice')]
    fields = {'q': FilterField(predicate=pred)}
    clauses = build_filter_clauses(tokens, model=SampleModel, fields=fields)
    assert 'ILIKE' in _render(clauses[0])

def test_build_filter_clauses_field_without_resolver_or_predicate_raises() -> None:
    tokens = [FilterToken(field='name', operator='eq', raw_value='x')]
    fields: dict[str, FilterField[SampleModel]] = {'name': FilterField()}
    with pytest.raises(ValueError, match='resolver or predicate'):
        build_filter_clauses(tokens, model=SampleModel, fields=fields)

def test_build_filter_clauses_empty_tokens_returns_empty() -> None:
    clauses = build_filter_clauses([], model=SampleModel, fields={})
    assert clauses == []

def test_build_filter_clauses_isnull_no_value() -> None:
    tokens = [FilterToken(field='name', operator='isnull', raw_value=None)]
    fields: dict[str, FilterField[SampleModel]] = {'name': FilterField(resolver=SampleModel.name)}
    clauses = build_filter_clauses(tokens, model=SampleModel, fields=fields)
    assert 'IS NULL' in _render(clauses[0])

def test_build_filter_clauses_in_operator_requires_value() -> None:
    tokens = [FilterToken(field='name', operator='in', raw_value=None)]
    fields: dict[str, FilterField[SampleModel]] = {'name': FilterField(resolver=SampleModel.name)}
    with pytest.raises(ValueError, match='requires a value'):
        build_filter_clauses(tokens, model=SampleModel, fields=fields)

def test_build_filter_clauses_non_isnull_without_value_raises() -> None:
    tokens = [FilterToken(field='name', operator='eq', raw_value=None)]
    fields: dict[str, FilterField[SampleModel]] = {'name': FilterField(resolver=SampleModel.name)}
    with pytest.raises(ValueError, match='requires a value'):
        build_filter_clauses(tokens, model=SampleModel, fields=fields)

def test_build_filter_clauses_callable_resolver_in_field() -> None:
    tokens = [FilterToken(field='name', operator='eq', raw_value='x')]
    fields: dict[str, FilterField[SampleModel]] = {'name': FilterField(resolver=lambda m: m.name, value_type=str)}
    clauses = build_filter_clauses(tokens, model=SampleModel, fields=fields)
    assert "sample_model.name = 'x'" in _render(clauses[0])

def test_build_sort_clauses_ascending() -> None:
    tokens = [SortToken(field='name', direction='asc')]
    fields: dict[str, SortField[SampleModel]] = {'name': SortField(resolver=SampleModel.name)}
    clauses = build_sort_clauses(tokens, model=SampleModel, fields=fields)
    assert len(clauses) == 1
    assert 'ASC' in _render(clauses[0])

def test_build_sort_clauses_descending() -> None:
    tokens = [SortToken(field='score', direction='desc')]
    fields: dict[str, SortField[SampleModel]] = {'score': SortField(resolver=SampleModel.score)}
    clauses = build_sort_clauses(tokens, model=SampleModel, fields=fields)
    assert 'DESC' in _render(clauses[0])

def test_build_sort_clauses_unknown_field_raises() -> None:
    tokens = [SortToken(field='unknown', direction='asc')]
    with pytest.raises(ValueError, match='Unsupported sort field'):
        build_sort_clauses(tokens, model=SampleModel, fields={})

def test_build_sort_clauses_empty_tokens_returns_empty() -> None:
    clauses = build_sort_clauses([], model=SampleModel, fields={})
    assert clauses == []

def test_build_sort_clauses_callable_resolver() -> None:
    tokens = [SortToken(field='name', direction='asc')]
    fields: dict[str, SortField[SampleModel]] = {'name': SortField(resolver=lambda m: m.name)}
    clauses = build_sort_clauses(tokens, model=SampleModel, fields=fields)
    assert 'sample_model.name' in _render(clauses[0])

def test_build_sort_clauses_multiple_tokens() -> None:
    tokens = [
        SortToken(field='name', direction='asc'),
        SortToken(field='score', direction='desc'),
    ]
    fields: dict[str, SortField[SampleModel]] = {
        'name': SortField(resolver=SampleModel.name),
        'score': SortField(resolver=SampleModel.score),
    }
    clauses = build_sort_clauses(tokens, model=SampleModel, fields=fields)
    assert len(clauses) == _MULTI_CLAUSE_COUNT

def test_query_input_negative_offset_raises() -> None:
    with pytest.raises(ValidationError, match='offset must be zero or a positive integer'):
        QueryInput(offset=-1)

def test_query_input_zero_offset_accepted() -> None:
    q = QueryInput(offset=0)
    assert q.offset == 0

def test_query_input_positive_offset_accepted() -> None:
    q = QueryInput(offset=_POSITIVE_OFFSET)
    assert q.offset == _POSITIVE_OFFSET

def test_query_input_none_limit_accepted() -> None:
    q = QueryInput(limit=None)
    assert q.limit is None

def test_query_input_positive_limit_accepted() -> None:
    q = QueryInput(limit=_POSITIVE_LIMIT)
    assert q.limit == _POSITIVE_LIMIT

def test_build_query_params_filters_without_filter_fields_raises() -> None:
    query = QueryInput(filter=['name:eq:x'])
    with pytest.raises(ValueError, match='Filter fields mapping is required'):
        build_query_params(query, model=SampleModel, filter_fields={})

def test_build_query_params_sort_without_sort_fields_raises() -> None:
    query = QueryInput(sort=['-score'])
    with pytest.raises(ValueError, match='Sort fields mapping is required'):
        build_query_params(query, model=SampleModel, sort_fields={})

def test_build_query_params_no_filter_no_sort_returns_none_for_both() -> None:
    query = QueryInput()
    params = build_query_params(query, model=SampleModel)
    assert params.filters is None
    assert params.ordering is None

def test_build_query_params_explicit_limit_and_offset_passed_through() -> None:
    query = QueryInput(limit=_LIMIT_SMALL, offset=_OFFSET_SMALL)
    params = build_query_params(query, model=SampleModel)
    assert params.limit == _LIMIT_SMALL
    assert params.offset == _OFFSET_SMALL

def test_build_query_params_base_query_forwarded() -> None:
    base = select(SampleModel)
    query = QueryInput()
    params = build_query_params(query, model=SampleModel, base_query=base)
    assert params.base_query is base
