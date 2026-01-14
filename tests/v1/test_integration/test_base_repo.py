from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from notora.v1.schemas.base import Filter
from tests.v1.test_integration.mocks.model import MockModel, MockModelFactory
from tests.v1.test_integration.mocks.repo import MockRepo


async def _setup(db_session: AsyncSession, count: int) -> list[MockModel]:
    objs = [MockModelFactory.build() for _ in range(count)]
    db_session.add_all(objs)
    await db_session.commit()
    return objs


async def _select_one(db_session: AsyncSession, pk: UUID) -> MockModel:
    query = select(MockModel).where(MockModel.id == pk)
    return (await db_session.scalars(query)).one()


async def test_select(db_session: AsyncSession, mock_repo: MockRepo) -> None:
    objs_count = 3
    objs = await _setup(db_session, objs_count)

    query = mock_repo.select()

    res = (await db_session.scalars(query)).all()
    assert len(res) == objs_count
    assert set(objs) == set(res)


async def test_create(db_session: AsyncSession, mock_repo: MockRepo) -> None:
    new_data = {'name': 'test'}

    query = mock_repo.create(new_data)

    res = (await db_session.scalars(query)).one()
    assert res.id is not None


async def test_retrieve(db_session: AsyncSession, mock_repo: MockRepo) -> None:
    objs = await _setup(db_session, 3)
    target_obj = objs[0]

    query = mock_repo.retrieve(target_obj.id)

    res = (await db_session.scalars(query)).one_or_none()
    assert res is not None
    assert res.id == target_obj.id


async def test_retrieve_by(db_session: AsyncSession, mock_repo: MockRepo) -> None:
    objs = await _setup(db_session, 3)
    target_obj = objs[0]

    query = mock_repo.retrieve_by(filters=[Filter(field='id', op='=', value=target_obj.id)])

    res = (await db_session.scalars(query)).one_or_none()
    assert res is not None
    assert res.id == target_obj.id


async def test_update(db_session: AsyncSession, mock_repo: MockRepo) -> None:
    objs = await _setup(db_session, 1)
    target_obj = objs[0]
    new_value = 'Updated Value'

    query = mock_repo.update(target_obj.id, {'name': new_value})
    result = await db_session.execute(query)
    result.scalars().all()
    await db_session.commit()

    updated_obj = await _select_one(db_session, target_obj.id)
    assert updated_obj.name == new_value


async def test_update_by(db_session: AsyncSession, mock_repo: MockRepo) -> None:
    objs = await _setup(db_session, 3)
    target_obj = objs[0]
    new_value = 'Updated Value'

    query = mock_repo.update_by(
        {'name': new_value}, filters=[Filter(field='id', op='=', value=target_obj.id)]
    )
    result = await db_session.execute(query)
    result.scalars().all()
    await db_session.commit()

    updated_obj = await _select_one(db_session, target_obj.id)
    assert updated_obj.name == new_value


async def test_hard_delete(db_session: AsyncSession, mock_repo: MockRepo) -> None:
    objs = await _setup(db_session, 1)
    target_obj = objs[0]

    query = mock_repo.hard_delete(target_obj.id)
    result = await db_session.execute(query)
    result.scalars().all()
    await db_session.commit()

    with pytest.raises(NoResultFound):
        await _select_one(db_session, target_obj.id)


async def test_hard_delete_by(db_session: AsyncSession, mock_repo: MockRepo) -> None:
    objs = await _setup(db_session, 3)
    ids_to_delete = [obj.id for obj in objs[:2]]  # Delete first two

    query = mock_repo.hard_delete_by(filters=[Filter(field='id', op='in', value=ids_to_delete)])
    result = await db_session.execute(query)
    result.scalars().all()
    await db_session.commit()

    # Ensure the deleted objects are no longer in the database
    for obj_id in ids_to_delete:
        with pytest.raises(NoResultFound):
            await _select_one(db_session, obj_id)

    # Verify the remaining object still exists
    assert await _select_one(db_session, objs[2].id)


async def test_number_of_records(db_session: AsyncSession, mock_repo: MockRepo) -> None:
    objs_count = 5
    await _setup(db_session, objs_count)

    query = mock_repo.number_of_records()

    total_count = (await db_session.scalars(query)).one()
    assert total_count == objs_count


async def test_soft_delete(db_session: AsyncSession, mock_repo: MockRepo) -> None:
    objs = await _setup(db_session, 1)
    obj_to_delete = objs[0]

    query = mock_repo.soft_delete(obj_to_delete.id)
    result = await db_session.execute(query)
    result.scalars().all()
    await db_session.commit()

    refreshed_obj = await db_session.get(MockModel, obj_to_delete.id)
    assert refreshed_obj
    assert refreshed_obj.deleted_at is not None


async def test_soft_delete_by(db_session: AsyncSession, mock_repo: MockRepo) -> None:
    objs = await _setup(db_session, 3)
    ids_to_delete = [obj.id for obj in objs[:2]]  # Delete first two

    query = mock_repo.soft_delete_by(filters=[Filter(field='id', op='in', value=ids_to_delete)])
    result = await db_session.execute(query)
    result.scalars().all()
    await db_session.commit()

    # Verify that the first two are marked as deleted
    for obj_id in ids_to_delete:
        obj = await _select_one(db_session, obj_id)
        assert obj.deleted_at is not None
    # Verify the third is still not deleted
    remaining_obj = await _select_one(db_session, objs[2].id)
    assert remaining_obj
    assert remaining_obj.deleted_at is None


async def test_select_excludes_deleted(db_session: AsyncSession, mock_repo: MockRepo) -> None:
    objs = await _setup(db_session, 2)

    # Soft delete one object
    obj_to_delete = objs[0]
    query = mock_repo.soft_delete(obj_to_delete.id)
    result = await db_session.execute(query)
    result.scalars().all()
    await db_session.commit()

    # Ensure only non-deleted objects are retrieved
    query = mock_repo.select()
    res = (await db_session.scalars(query)).all()
    assert len(res) == 1
    assert res[0].id != obj_to_delete.id


async def test_soft_delete_is_not_hard(db_session: AsyncSession, mock_repo: MockRepo) -> None:
    objs_count = 3
    objs = await _setup(db_session, objs_count)

    # Soft delete one object
    obj_to_delete = objs[0]
    query = mock_repo.soft_delete(obj_to_delete.id)
    result = await db_session.execute(query)
    result.scalars().all()
    await db_session.commit()

    # Check that all objects (including deleted) can be retrieved
    res = (await db_session.scalars(select(mock_repo.model))).all()
    assert len(res) == objs_count
    assert obj_to_delete in res
