"""Tests for PayloadMixin._dump_payload."""

from pydantic import BaseModel as PydanticModel

from notora.v2.services.mixins.payload import PayloadMixin


class _SomeSchema(PydanticModel):
    name: str
    score: int = 0


class _Mixin(PayloadMixin):
    pass


class TestDumpPayload:
    def test_dict_input_returned_as_copy(self) -> None:
        original = {'name': 'Alice', 'score': 5}
        result = _Mixin._dump_payload(original, exclude_unset=True)
        assert result == original
        # Ensure it's a copy, not the same object
        result['name'] = 'Bob'
        assert original['name'] == 'Alice'

    def test_pydantic_model_dump_with_exclude_unset_true(self) -> None:
        schema = _SomeSchema(name='Alice')
        result = _Mixin._dump_payload(schema, exclude_unset=True)
        # 'score' was not explicitly set, so it should be excluded
        assert 'name' in result
        assert 'score' not in result

    def test_pydantic_model_dump_with_exclude_unset_false(self) -> None:
        schema = _SomeSchema(name='Alice')
        result = _Mixin._dump_payload(schema, exclude_unset=False)
        assert result == {'name': 'Alice', 'score': 0}

    def test_pydantic_model_fully_set(self) -> None:
        schema = _SomeSchema(name='Bob', score=10)
        result = _Mixin._dump_payload(schema, exclude_unset=True)
        assert result == {'name': 'Bob', 'score': 10}

    def test_empty_dict_returns_empty_dict(self) -> None:
        result = _Mixin._dump_payload({}, exclude_unset=False)
        assert result == {}

    def test_non_string_dict_values_preserved(self) -> None:
        payload = {'count': 42, 'active': True, 'tags': ['a', 'b']}
        result = _Mixin._dump_payload(payload, exclude_unset=True)
        assert result == payload
