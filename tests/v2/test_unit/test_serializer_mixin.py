"""Tests for SerializerMixin — edge cases not covered by integration tests."""

import types

import pytest
from pydantic import ConfigDict

from notora.v2.models.base import GenericBaseModel
from notora.v2.schemas.base import BaseResponseSchema
from notora.v2.services.mixins.serializer import SerializerMixin


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


class TestSerializeOne:
    def test_uses_explicit_schema_arg(self) -> None:
        mixin = _make_mixin()
        item = _make_obj()
        result = mixin.serialize_one(item, schema=_DetailSchema)
        assert isinstance(result, _DetailSchema)

    def test_falls_back_to_detail_schema_attribute(self) -> None:
        mixin = _make_mixin()
        mixin.detail_schema = _DetailSchema
        item = _make_obj()
        result = mixin.serialize_one(item)
        assert isinstance(result, _DetailSchema)

    def test_raises_when_no_schema_and_no_detail_schema(self) -> None:
        mixin = _make_mixin()
        item = _make_obj()
        with pytest.raises(ValueError, match='schema is required'):
            mixin.serialize_one(item)

    def test_explicit_schema_overrides_detail_schema(self) -> None:
        mixin = _make_mixin()
        mixin.detail_schema = _DetailSchema

        class _AltSchema(_DetailSchema):
            pass

        item = _make_obj()
        result = mixin.serialize_one(item, schema=_AltSchema)
        assert isinstance(result, _AltSchema)


class TestSerializeMany:
    def test_empty_list_returns_empty(self) -> None:
        mixin = _make_mixin()
        mixin.list_schema = _ListSchema
        result = mixin.serialize_many([])
        assert result == []

    def test_uses_list_schema_by_default(self) -> None:
        mixin = _make_mixin()
        mixin.list_schema = _ListSchema
        item = _make_obj()
        results = mixin.serialize_many([item])
        assert all(isinstance(r, _ListSchema) for r in results)

    def test_falls_back_to_detail_schema_when_list_schema_absent(self) -> None:
        mixin = _make_mixin()
        mixin.detail_schema = _DetailSchema
        item = _make_obj()
        results = mixin.serialize_many([item])
        assert all(isinstance(r, _DetailSchema) for r in results)

    def test_explicit_schema_arg_overrides_list_schema(self) -> None:
        mixin = _make_mixin()
        mixin.list_schema = _ListSchema

        class _AltSchema(_ListSchema):
            pass

        item = _make_obj()
        results = mixin.serialize_many([item], schema=_AltSchema)
        assert all(isinstance(r, _AltSchema) for r in results)

    def test_prefer_list_schema_false_uses_explicit_schema_only(self) -> None:
        mixin = _make_mixin()
        mixin.detail_schema = _DetailSchema
        mixin.list_schema = _ListSchema
        item = _make_obj()
        results = mixin.serialize_many([item], schema=_DetailSchema, prefer_list_schema=False)
        assert all(isinstance(r, _DetailSchema) for r in results)

    def test_raises_when_no_schema_at_all(self) -> None:
        mixin = _make_mixin()
        item = _make_obj()
        with pytest.raises(ValueError, match='schema is required'):
            mixin.serialize_many([item])

    def test_prefer_list_schema_false_and_no_explicit_schema_raises(self) -> None:
        mixin = _make_mixin()
        mixin.detail_schema = None
        mixin.list_schema = None
        item = _make_obj()
        with pytest.raises(ValueError, match='schema is required'):
            mixin.serialize_many([item], prefer_list_schema=False)

    def test_serializes_multiple_items(self) -> None:
        mixin = _make_mixin()
        mixin.list_schema = _ListSchema
        items = [_make_obj() for _ in range(5)]
        results = mixin.serialize_many(items)
        assert len(results) == 5
