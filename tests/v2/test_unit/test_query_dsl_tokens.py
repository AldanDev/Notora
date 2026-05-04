"""Tests for query_dsl token parsers, apply_filter_operator, build_filter_clauses, and build_sort_clauses."""

import pytest
from pydantic import ValidationError
from sqlalchemy import Integer, String
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


# ---------------------------------------------------------------------------
# parse_filter_token
# ---------------------------------------------------------------------------

class TestParseFilterToken:
    def test_parses_field_op_value(self) -> None:
        token = parse_filter_token('name:eq:alice')
        assert token.field == 'name'
        assert token.operator == 'eq'
        assert token.raw_value == 'alice'

    def test_parses_operator_only_for_isnull(self) -> None:
        token = parse_filter_token('name:isnull')
        assert token.field == 'name'
        assert token.operator == 'isnull'
        assert token.raw_value is None

    def test_raises_for_missing_colon(self) -> None:
        with pytest.raises(ValueError, match='"field:op:value"'):
            parse_filter_token('nocolon')

    def test_raises_for_empty_field_name(self) -> None:
        with pytest.raises(ValueError, match='field name cannot be empty'):
            parse_filter_token(':eq:value')

    def test_raises_for_unsupported_operator(self) -> None:
        with pytest.raises(ValueError, match='Unsupported filter operator'):
            parse_filter_token('name:contains:hello')

    def test_value_with_colons_preserved(self) -> None:
        token = parse_filter_token('name:eq:a:b:c')
        assert token.raw_value == 'a:b:c'

    def test_whitespace_stripped_from_field_and_op(self) -> None:
        token = parse_filter_token(' name : eq : alice ')
        assert token.field == 'name'
        assert token.operator == 'eq'

    def test_whitespace_only_value_becomes_none(self) -> None:
        token = parse_filter_token('name:eq:   ')
        assert token.raw_value is None

    def test_all_operators_accepted(self) -> None:
        valid_ops = ('eq', 'ne', 'lt', 'lte', 'gt', 'gte', 'in', 'ilike', 'isnull')
        for op in valid_ops:
            token = parse_filter_token(f'name:{op}:x')
            assert token.operator == op

    def test_isnull_with_false_value(self) -> None:
        token = parse_filter_token('name:isnull:false')
        assert token.raw_value == 'false'

    def test_in_with_comma_separated_value(self) -> None:
        token = parse_filter_token('score:in:1,2,3')
        assert token.raw_value == '1,2,3'


# ---------------------------------------------------------------------------
# parse_sort_token
# ---------------------------------------------------------------------------

class TestParseSortToken:
    def test_plain_field_is_ascending(self) -> None:
        token = parse_sort_token('name')
        assert token.field == 'name'
        assert token.direction == 'asc'

    def test_plus_prefix_is_ascending(self) -> None:
        token = parse_sort_token('+name')
        assert token.field == 'name'
        assert token.direction == 'asc'

    def test_minus_prefix_is_descending(self) -> None:
        token = parse_sort_token('-score')
        assert token.field == 'score'
        assert token.direction == 'desc'

    def test_empty_string_raises(self) -> None:
        with pytest.raises(ValueError, match='cannot be empty'):
            parse_sort_token('')

    def test_only_minus_raises(self) -> None:
        with pytest.raises(ValueError, match='cannot be empty'):
            parse_sort_token('-')

    def test_only_plus_raises(self) -> None:
        with pytest.raises(ValueError, match='cannot be empty'):
            parse_sort_token('+')

    def test_whitespace_stripped(self) -> None:
        token = parse_sort_token('  name  ')
        assert token.field == 'name'

    def test_returns_sort_token_dataclass(self) -> None:
        token = parse_sort_token('name')
        assert isinstance(token, SortToken)


# ---------------------------------------------------------------------------
# apply_filter_operator
# ---------------------------------------------------------------------------

class TestApplyFilterOperator:
    def test_eq(self) -> None:
        clause = apply_filter_operator(SampleModel.name, 'eq', 'alice')
        assert "sample_model.name = 'alice'" in _render(clause)

    def test_ne(self) -> None:
        clause = apply_filter_operator(SampleModel.name, 'ne', 'alice')
        rendered = _render(clause)
        assert 'sample_model.name' in rendered
        assert '!=' in rendered or '<>' in rendered

    def test_lt(self) -> None:
        clause = apply_filter_operator(SampleModel.score, 'lt', 5)
        assert 'sample_model.score < 5' in _render(clause)

    def test_lte(self) -> None:
        clause = apply_filter_operator(SampleModel.score, 'lte', 5)
        assert 'sample_model.score <= 5' in _render(clause)

    def test_gt(self) -> None:
        clause = apply_filter_operator(SampleModel.score, 'gt', 5)
        assert 'sample_model.score > 5' in _render(clause)

    def test_gte(self) -> None:
        clause = apply_filter_operator(SampleModel.score, 'gte', 5)
        assert 'sample_model.score >= 5' in _render(clause)

    def test_in(self) -> None:
        clause = apply_filter_operator(SampleModel.score, 'in', [1, 2, 3])
        assert 'IN' in _render(clause)

    def test_ilike(self) -> None:
        clause = apply_filter_operator(SampleModel.name, 'ilike', '%alice%')
        assert 'ILIKE' in _render(clause)

    def test_isnull_true(self) -> None:
        clause = apply_filter_operator(SampleModel.name, 'isnull', True)
        assert 'IS NULL' in _render(clause)

    def test_isnull_false(self) -> None:
        clause = apply_filter_operator(SampleModel.name, 'isnull', False)
        assert 'IS NOT NULL' in _render(clause)

    def test_unsupported_operator_raises(self) -> None:
        with pytest.raises(ValueError, match='Unsupported filter operator'):
            apply_filter_operator(SampleModel.name, 'contains', 'x')  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# resolve_to_column
# ---------------------------------------------------------------------------

class TestResolveToColumn:
    def test_direct_column_returned_unchanged(self) -> None:
        col = resolve_to_column(SampleModel.name, SampleModel)
        assert 'sample_model.name' in str(col)

    def test_callable_resolver_called_with_model(self) -> None:
        col = resolve_to_column(lambda m: m.score, SampleModel)
        assert 'sample_model.score' in str(col)


# ---------------------------------------------------------------------------
# build_filter_clauses
# ---------------------------------------------------------------------------

class TestBuildFilterClauses:
    def test_single_eq_clause(self) -> None:
        tokens = [FilterToken(field='name', operator='eq', raw_value='alice')]
        fields = {'name': FilterField(resolver=SampleModel.name, value_type=str)}
        clauses = build_filter_clauses(tokens, model=SampleModel, fields=fields)
        assert len(clauses) == 1
        assert "sample_model.name = 'alice'" in _render(clauses[0])

    def test_unknown_field_raises(self) -> None:
        tokens = [FilterToken(field='unknown', operator='eq', raw_value='x')]
        with pytest.raises(ValueError, match='Unsupported filter field'):
            build_filter_clauses(tokens, model=SampleModel, fields={})

    def test_disallowed_operator_raises(self) -> None:
        tokens = [FilterToken(field='name', operator='gt', raw_value='5')]
        fields = {'name': FilterField(resolver=SampleModel.name, operators=frozenset({'eq'}))}
        with pytest.raises(ValueError, match='Operator'):
            build_filter_clauses(tokens, model=SampleModel, fields=fields)

    def test_predicate_field(self) -> None:
        def pred(model: type[SampleModel], _op: str, value: str) -> ColumnElement[bool]:
            return model.name.ilike(f'%{value}%')

        tokens = [FilterToken(field='q', operator='eq', raw_value='alice')]
        fields = {'q': FilterField(predicate=pred)}
        clauses = build_filter_clauses(tokens, model=SampleModel, fields=fields)
        assert 'ILIKE' in _render(clauses[0])

    def test_field_without_resolver_or_predicate_raises(self) -> None:
        tokens = [FilterToken(field='name', operator='eq', raw_value='x')]
        fields = {'name': FilterField()}
        with pytest.raises(ValueError, match='resolver or predicate'):
            build_filter_clauses(tokens, model=SampleModel, fields=fields)

    def test_empty_tokens_returns_empty(self) -> None:
        clauses = build_filter_clauses([], model=SampleModel, fields={})
        assert clauses == []

    def test_isnull_no_value(self) -> None:
        tokens = [FilterToken(field='name', operator='isnull', raw_value=None)]
        fields = {'name': FilterField(resolver=SampleModel.name)}
        clauses = build_filter_clauses(tokens, model=SampleModel, fields=fields)
        assert 'IS NULL' in _render(clauses[0])

    def test_in_operator_requires_value(self) -> None:
        tokens = [FilterToken(field='name', operator='in', raw_value=None)]
        fields = {'name': FilterField(resolver=SampleModel.name)}
        with pytest.raises(ValueError, match='requires a value'):
            build_filter_clauses(tokens, model=SampleModel, fields=fields)

    def test_non_isnull_without_value_raises(self) -> None:
        tokens = [FilterToken(field='name', operator='eq', raw_value=None)]
        fields = {'name': FilterField(resolver=SampleModel.name)}
        with pytest.raises(ValueError, match='requires a value'):
            build_filter_clauses(tokens, model=SampleModel, fields=fields)

    def test_callable_resolver_in_field(self) -> None:
        tokens = [FilterToken(field='name', operator='eq', raw_value='x')]
        fields = {'name': FilterField(resolver=lambda m: m.name, value_type=str)}
        clauses = build_filter_clauses(tokens, model=SampleModel, fields=fields)
        assert "sample_model.name = 'x'" in _render(clauses[0])


# ---------------------------------------------------------------------------
# build_sort_clauses
# ---------------------------------------------------------------------------

class TestBuildSortClauses:
    def test_ascending(self) -> None:
        tokens = [SortToken(field='name', direction='asc')]
        fields = {'name': SortField(resolver=SampleModel.name)}
        clauses = build_sort_clauses(tokens, model=SampleModel, fields=fields)
        assert len(clauses) == 1
        assert 'ASC' in _render(clauses[0])

    def test_descending(self) -> None:
        tokens = [SortToken(field='score', direction='desc')]
        fields = {'score': SortField(resolver=SampleModel.score)}
        clauses = build_sort_clauses(tokens, model=SampleModel, fields=fields)
        assert 'DESC' in _render(clauses[0])

    def test_unknown_field_raises(self) -> None:
        tokens = [SortToken(field='unknown', direction='asc')]
        with pytest.raises(ValueError, match='Unsupported sort field'):
            build_sort_clauses(tokens, model=SampleModel, fields={})

    def test_empty_tokens_returns_empty(self) -> None:
        clauses = build_sort_clauses([], model=SampleModel, fields={})
        assert clauses == []

    def test_callable_resolver(self) -> None:
        tokens = [SortToken(field='name', direction='asc')]
        fields = {'name': SortField(resolver=lambda m: m.name)}
        clauses = build_sort_clauses(tokens, model=SampleModel, fields=fields)
        assert 'sample_model.name' in _render(clauses[0])

    def test_multiple_tokens(self) -> None:
        tokens = [
            SortToken(field='name', direction='asc'),
            SortToken(field='score', direction='desc'),
        ]
        fields = {
            'name': SortField(resolver=SampleModel.name),
            'score': SortField(resolver=SampleModel.score),
        }
        clauses = build_sort_clauses(tokens, model=SampleModel, fields=fields)
        assert len(clauses) == 2


# ---------------------------------------------------------------------------
# QueryInput validation
# ---------------------------------------------------------------------------

class TestQueryInput:
    def test_negative_offset_raises(self) -> None:
        with pytest.raises(ValidationError, match='offset must be zero or a positive integer'):
            QueryInput(offset=-1)

    def test_zero_offset_accepted(self) -> None:
        q = QueryInput(offset=0)
        assert q.offset == 0

    def test_positive_offset_accepted(self) -> None:
        q = QueryInput(offset=100)
        assert q.offset == 100

    def test_none_limit_accepted(self) -> None:
        q = QueryInput(limit=None)
        assert q.limit is None

    def test_positive_limit_accepted(self) -> None:
        q = QueryInput(limit=50)
        assert q.limit == 50


# ---------------------------------------------------------------------------
# build_query_params edge cases
# ---------------------------------------------------------------------------

class TestBuildQueryParamsEdgeCases:
    def test_filters_present_without_filter_fields_raises(self) -> None:
        query = QueryInput(filter=['name:eq:x'])
        with pytest.raises(ValueError, match='Filter fields mapping is required'):
            build_query_params(query, model=SampleModel, filter_fields={})

    def test_sort_present_without_sort_fields_raises(self) -> None:
        query = QueryInput(sort=['-score'])
        with pytest.raises(ValueError, match='Sort fields mapping is required'):
            build_query_params(query, model=SampleModel, sort_fields={})

    def test_no_filter_no_sort_returns_none_filters_and_ordering(self) -> None:
        query = QueryInput()
        params = build_query_params(query, model=SampleModel)
        assert params.filters is None
        assert params.ordering is None

    def test_explicit_limit_is_passed_through(self) -> None:
        query = QueryInput(limit=5, offset=10)
        params = build_query_params(query, model=SampleModel)
        assert params.limit == 5
        assert params.offset == 10

    def test_base_query_forwarded(self) -> None:
        from sqlalchemy import select
        base = select(SampleModel)
        query = QueryInput()
        params = build_query_params(query, model=SampleModel, base_query=base)
        assert params.base_query is base
