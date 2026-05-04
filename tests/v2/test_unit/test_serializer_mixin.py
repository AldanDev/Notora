"""Tests for SerializerMixin — edge cases not covered by integration tests."""

import types

import pytest
from pydantic import ConfigDict

from notora.v2.models.base import GenericBaseModel
from notora.v2.schemas.base import BaseResponseSchema
from notora.v2.services.mixins.serializer import SerializerMixin

_ITEM_COUNT = 5

class _Item(GenericBaseModel):
    pass

class _DetailSchema(BaseResponseSchema):
    model_config = ConfigDict(from_attributes=True)

class _ListSchema(BaseResponseSchema):
    model_config = ConfigDict(from_attributes=True)

# A plain namespace satisfies `from_attributes=True` schemas that have no required fields.
def _make_obj() -> types.SimpleNamespace:
    return types.SimpleNamespace()

def _make_mixin() -> SerializerMixin[_Item, _DetailSchema, _ListSchema]:
    mixin: SerializerMixin[_Item, _DetailSchema, _ListSchema] = SerializerMixin()
    return mixin

def test_serialize_one_uses_explicit_schema_arg() -> None:
    mixin = _make_mixin()
    item = _make_obj()
    result = mixin.serialize_one(item, schema=_DetailSchema)
    assert isinstance(result, _DetailSchema)

def test_serialize_one_falls_back_to_detail_schema_attribute() -> None:
    mixin = _make_mixin()
    mixin.detail_schema = _DetailSchema
    item = _make_obj()
    result = mixin.serialize_one(item)
    assert isinstance(result, _DetailSchema)

def test_serialize_one_raises_when_no_schema_and_no_detail_schema() -> None:
    mixin = _make_mixin()
    item = _make_obj()
    with pytest.raises(ValueError, match='schema is required'):
        mixin.serialize_one(item)

def test_serialize_one_explicit_schema_overrides_detail_schema() -> None:
    mixin = _make_mixin()
    mixin.detail_schema = _DetailSchema

    class _AltSchema(_DetailSchema):
        pass

    item = _make_obj()
    result = mixin.serialize_one(item, schema=_AltSchema)
    assert isinstance(result, _AltSchema)

def test_serialize_many_empty_list_returns_empty() -> None:
    mixin = _make_mixin()
    mixin.list_schema = _ListSchema
    result = mixin.serialize_many([])
    assert result == []

def test_serialize_many_uses_list_schema_by_default() -> None:
    mixin = _make_mixin()
    mixin.list_schema = _ListSchema
    item = _make_obj()
    results = mixin.serialize_many([item])
    assert all(isinstance(r, _ListSchema) for r in results)

def test_serialize_many_falls_back_to_detail_schema_when_list_schema_absent() -> None:
    mixin = _make_mixin()
    mixin.detail_schema = _DetailSchema
    item = _make_obj()
    results = mixin.serialize_many([item])
    assert all(isinstance(r, _DetailSchema) for r in results)

def test_serialize_many_explicit_schema_arg_overrides_list_schema() -> None:
    mixin = _make_mixin()
    mixin.list_schema = _ListSchema

    class _AltSchema(_ListSchema):
        pass

    item = _make_obj()
    results = mixin.serialize_many([item], schema=_AltSchema)
    assert all(isinstance(r, _AltSchema) for r in results)

def test_serialize_many_prefer_list_schema_false_uses_explicit_schema() -> None:
    mixin = _make_mixin()
    mixin.detail_schema = _DetailSchema
    mixin.list_schema = _ListSchema
    item = _make_obj()
    results = mixin.serialize_many([item], schema=_DetailSchema, prefer_list_schema=False)
    assert all(isinstance(r, _DetailSchema) for r in results)

def test_serialize_many_raises_when_no_schema_at_all() -> None:
    mixin = _make_mixin()
    item = _make_obj()
    with pytest.raises(ValueError, match='schema is required'):
        mixin.serialize_many([item])

def test_serialize_many_prefer_list_schema_false_no_schema_raises() -> None:
    mixin = _make_mixin()
    mixin.detail_schema = None
    mixin.list_schema = None
    item = _make_obj()
    with pytest.raises(ValueError, match='schema is required'):
        mixin.serialize_many([item], prefer_list_schema=False)

def test_serialize_many_serializes_multiple_items() -> None:
    mixin = _make_mixin()
    mixin.list_schema = _ListSchema
    items = [_make_obj() for _ in range(_ITEM_COUNT)]
    results = mixin.serialize_many(items)
    assert len(results) == _ITEM_COUNT
