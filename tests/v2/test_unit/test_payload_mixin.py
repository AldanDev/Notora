"""Tests for PayloadMixin._dump_payload."""

from pydantic import BaseModel as PydanticModel

from notora.v2.services.mixins.payload import PayloadMixin


class _SomeSchema(PydanticModel):
    name: str
    score: int = 0


def test_payload_mixin_dict_input_returned_as_copy() -> None:
    original = {'name': 'Alice', 'score': 5}
    result = PayloadMixin._dump_payload(original, exclude_unset=True)
    assert result == original
    # Ensure it's a copy, not the same object
    result['name'] = 'Bob'
    assert original['name'] == 'Alice'


def test_payload_mixin_pydantic_model_dump_with_exclude_unset_true() -> None:
    schema = _SomeSchema(name='Alice')
    result = PayloadMixin._dump_payload(schema, exclude_unset=True)
    # 'score' was not explicitly set, so it should be excluded
    assert 'name' in result
    assert 'score' not in result


def test_payload_mixin_pydantic_model_dump_with_exclude_unset_false() -> None:
    schema = _SomeSchema(name='Alice')
    result = PayloadMixin._dump_payload(schema, exclude_unset=False)
    assert result == {'name': 'Alice', 'score': 0}


def test_payload_mixin_pydantic_model_fully_set() -> None:
    score = 10
    schema = _SomeSchema(name='Bob', score=score)
    result = PayloadMixin._dump_payload(schema, exclude_unset=True)
    assert result == {'name': 'Bob', 'score': score}


def test_payload_mixin_empty_dict_returns_empty_dict() -> None:
    result = PayloadMixin._dump_payload({}, exclude_unset=False)
    assert result == {}


def test_payload_mixin_non_string_dict_values_preserved() -> None:
    payload = {'count': 42, 'active': True, 'tags': ['a', 'b']}
    result = PayloadMixin._dump_payload(payload, exclude_unset=True)
    assert result == payload
