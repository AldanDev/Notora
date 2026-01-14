from math import ceil
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from notora.v1.schemas.base import Filter
from tests.v1.test_integration.mocks.model import MockModel, MockModelFactory
from tests.v1.test_integration.mocks.schema import (
    CreateMockModelRequestSchema,
    MockModelResponseSchema,
    UpdateMockModelRequestSchema,
)
from tests.v1.test_integration.mocks.service import MockService


async def _setup(db_session: AsyncSession, count: int) -> list[MockModel]:
    objs = [MockModelFactory.build() for _ in range(count)]
    db_session.add_all(objs)
    await db_session.commit()
    return objs


async def _select_one(db_session: AsyncSession, pk: UUID) -> MockModel:
    query = select(MockModel).where(MockModel.id == pk)
    return (await db_session.scalars(query)).one()


def test_serialize(mock_service: MockService) -> None:
    db_obj = MockModelFactory.build()

    schema_obj = mock_service.serialize(db_obj)

    assert isinstance(schema_obj, MockModelResponseSchema)


def test_serialize_many(mock_service: MockService) -> None:
    objs_count = 5
    db_objs = [MockModelFactory.build() for _ in range(objs_count)]

    schema_objs = mock_service.serialize_many(db_objs)

    assert len(schema_objs) == objs_count
    assert all(isinstance(obj, MockModelResponseSchema) for obj in schema_objs)


async def test_list(db_session: AsyncSession, mock_service: MockService) -> None:
    objs_count = 5
    await _setup(db_session, objs_count)

    items = await mock_service.list_(db_session, limit=objs_count)

    assert len(items) == objs_count
    assert all(isinstance(item, MockModelResponseSchema) for item in items)


async def test_paginate(db_session: AsyncSession, mock_service: MockService) -> None:
    limit = 5
    offset = 0
    objs_count = 10
    await _setup(db_session, objs_count)

    res = await mock_service.paginate(db_session, limit=limit, offset=offset)

    assert res.meta.limit == limit
    assert res.meta.total == objs_count
    assert res.meta.current_page == 1
    assert res.meta.last_page == ceil(objs_count / limit)
    assert len(res.data) == limit
    assert all(isinstance(item, MockModelResponseSchema) for item in res.data)


async def test_create(db_session: AsyncSession, mock_service: MockService) -> None:
    new_data = CreateMockModelRequestSchema(name='test')

    created_obj = await mock_service.create(db_session, new_data)

    res = await _select_one(db_session, created_obj.id)
    assert res.id is not None


async def test_retrieve(db_session: AsyncSession, mock_service: MockService) -> None:
    objs = await _setup(db_session, 3)
    target_obj = objs[0]

    retrieved_obj = await mock_service.retrieve(db_session, target_obj.id)

    res = await _select_one(db_session, retrieved_obj.id)
    assert res.id == retrieved_obj.id


async def test_retrieve_one_by(db_session: AsyncSession, mock_service: MockService) -> None:
    objs = await _setup(db_session, 3)
    target_obj = objs[0]

    retrieved_obj = await mock_service.retrieve_one_by(
        db_session, filters=[Filter(field='id', op='=', value=target_obj.id)]
    )

    res = await _select_one(db_session, retrieved_obj.id)
    assert res.id == retrieved_obj.id


async def test_update(db_session: AsyncSession, mock_service: MockService) -> None:
    objs = await _setup(db_session, 1)
    target_obj = objs[0]
    new_data = UpdateMockModelRequestSchema(name='test')

    await mock_service.update(db_session, new_data, target_obj.id)

    res = await _select_one(db_session, target_obj.id)
    assert res.name == new_data.name


async def test_soft_delete(db_session: AsyncSession, mock_service: MockService) -> None:
    objs = await _setup(db_session, 1)
    target_obj = objs[0]

    deleted_obj = await mock_service.soft_delete(db_session, target_obj.id)

    assert deleted_obj is not None
    assert isinstance(deleted_obj, MockModel)
    assert deleted_obj.deleted_at is not None


async def test_soft_delete_one_by(db_session: AsyncSession, mock_service: MockService) -> None:
    objs = await _setup(db_session, 1)
    target_obj = objs[0]

    deleted_obj = await mock_service.soft_delete_one_by(
        db_session, filters=[Filter(field='id', op='=', value=target_obj.id)]
    )

    assert deleted_obj is not None
    assert isinstance(deleted_obj, MockModel)
    assert deleted_obj.deleted_at is not None
