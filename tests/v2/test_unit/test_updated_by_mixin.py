"""Tests for UpdatedByServiceMixin."""

from uuid import uuid4

import pytest
from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.base import Repository
from notora.v2.services.mixins.updated_by import UpdatedByServiceMixin


class _WithUpdatedBy(GenericBaseModel):
    name: Mapped[str] = mapped_column(String)
    updated_by: Mapped[object] = mapped_column(Uuid, nullable=True)


class _WithoutUpdatedBy(GenericBaseModel):
    name: Mapped[str] = mapped_column(String)


class _Mixin(UpdatedByServiceMixin[object, _WithUpdatedBy]):
    def __init__(self) -> None:
        self.repo = Repository[object, _WithUpdatedBy](_WithUpdatedBy)


class _MixinNoAttr(UpdatedByServiceMixin[object, _WithoutUpdatedBy]):
    def __init__(self) -> None:
        self.repo = Repository[object, _WithoutUpdatedBy](_WithoutUpdatedBy)


def test_apply_updated_by_actor_id_none_returns_payload_unchanged() -> None:
    mixin = _Mixin()
    payload = {'name': 'Alice'}
    result = mixin._apply_updated_by(payload, actor_id=None)
    assert result == {'name': 'Alice'}


def test_apply_updated_by_actor_id_set_injects_updated_by() -> None:
    mixin = _Mixin()
    actor_id = uuid4()
    payload: dict[str, object] = {'name': 'Alice'}
    result = mixin._apply_updated_by(payload, actor_id=actor_id)
    assert result['updated_by'] == actor_id


def test_apply_updated_by_existing_value_not_overwritten() -> None:
    mixin = _Mixin()
    original_actor = uuid4()
    new_actor = uuid4()
    payload: dict[str, object] = {'name': 'Alice', 'updated_by': original_actor}
    result = mixin._apply_updated_by(payload, actor_id=new_actor)
    assert result['updated_by'] == original_actor


def test_apply_updated_by_model_without_attribute_raises() -> None:
    mixin = _MixinNoAttr()
    payload: dict[str, object] = {'name': 'Bob'}
    with pytest.raises(ValueError, match='is not defined on'):
        mixin._apply_updated_by(payload, actor_id=uuid4())


def test_apply_updated_by_custom_attribute_name_used() -> None:
    class _WithCustomAttr(GenericBaseModel):
        name: Mapped[str] = mapped_column(String)
        modified_by: Mapped[object] = mapped_column(Uuid, nullable=True)

    class _CustomMixin(UpdatedByServiceMixin[object, _WithCustomAttr]):
        updated_by_attribute = 'modified_by'

        def __init__(self) -> None:
            self.repo = Repository[object, _WithCustomAttr](_WithCustomAttr)

    mixin = _CustomMixin()
    actor_id = uuid4()
    payload: dict[str, object] = {'name': 'Charlie'}
    result = mixin._apply_updated_by(payload, actor_id=actor_id)
    assert result['modified_by'] == actor_id
