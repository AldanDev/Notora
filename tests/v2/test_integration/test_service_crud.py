from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from notora.v2.exceptions.common import AlreadyExistsError, NotFoundError
from notora.v2.repositories.params import PaginationParams, QueryParams
from notora.v2.schemas.base import PaginatedResponseSchema
from tests.v2.test_integration.mocks.model import V2User
from tests.v2.test_integration.mocks.schema import V2UserCreateSchema, V2UserResponseSchema
from tests.v2.test_integration.mocks.service import V2UserService


def _create_user_payload(email: str, name: str) -> V2UserCreateSchema:
    return V2UserCreateSchema(id=uuid4(), email=email, name=name, is_active=True)


async def test_service_create_update_and_updated_by(
    db_session: AsyncSession,
    user_service: V2UserService,
) -> None:
    actor_id = uuid4()
    payload = _create_user_payload('service@ex.com', 'Service')

    created = await user_service.create(db_session, payload, actor_id=actor_id)
    await db_session.commit()

    assert isinstance(created, V2UserResponseSchema)
    assert created.updated_by == actor_id

    new_actor_id = uuid4()
    updated = await user_service.update(
        db_session,
        created.id,
        {'name': 'Service Updated'},
        actor_id=new_actor_id,
    )
    await db_session.commit()

    assert isinstance(updated, V2UserResponseSchema)
    assert updated.updated_by == new_actor_id

    refreshed = await db_session.get(V2User, created.id)
    assert refreshed is not None
    assert refreshed.updated_by == new_actor_id


async def test_service_update_by_and_soft_delete(
    db_session: AsyncSession,
    user_service: V2UserService,
) -> None:
    payload = _create_user_payload('update-by@ex.com', 'Before')
    created = await user_service.create(db_session, payload)
    await db_session.commit()

    assert isinstance(created, V2UserResponseSchema)
    updated = await user_service.update_by(
        db_session,
        filters=[V2User.email == payload.email],
        data={'name': 'After'},
    )
    await db_session.commit()

    assert isinstance(updated, V2UserResponseSchema)
    assert updated.name == 'After'

    deleted = await user_service.soft_delete(db_session, created.id)
    await db_session.commit()

    assert isinstance(deleted, V2UserResponseSchema)
    assert deleted.id == created.id

    refreshed = await db_session.get(V2User, created.id)
    assert refreshed is not None
    assert refreshed.deleted_at is not None


async def test_service_list_and_paginate_params(
    db_session: AsyncSession,
    user_service: V2UserService,
) -> None:
    payloads = [
        _create_user_payload('a@ex.com', 'A'),
        _create_user_payload('b@ex.com', 'B'),
        _create_user_payload('c@ex.com', 'C'),
    ]
    for payload in payloads:
        await user_service.create(db_session, payload)
    await db_session.commit()

    params = QueryParams[V2User](
        filters=[V2User.email != 'b@ex.com'],
        ordering=[V2User.email.asc()],
        limit=None,
    )
    items = await user_service.list_params(db_session, params)

    assert isinstance(items[0], V2UserResponseSchema)
    assert [item.email for item in items] == ['a@ex.com', 'c@ex.com']

    limit = 2
    page = await user_service.paginate(
        db_session,
        limit=limit,
        offset=0,
    )
    assert isinstance(page, PaginatedResponseSchema)
    assert page.meta.total == len(payloads)
    assert len(page.data) == limit

    limit_param = 1
    page_params = await user_service.paginate_params(
        db_session,
        PaginationParams[V2User](limit=limit_param, offset=1),
    )
    assert page_params.meta.offset == limit_param


async def test_service_retrieve_create_or_skip_upsert_and_delete(
    db_session: AsyncSession,
    user_service: V2UserService,
) -> None:
    payload = _create_user_payload('retrieve@ex.com', 'Retrieve')
    created = await user_service.create(db_session, payload)
    await db_session.commit()

    assert isinstance(created, V2UserResponseSchema)

    retrieved = await user_service.retrieve(db_session, created.id)
    assert isinstance(retrieved, V2UserResponseSchema)

    retrieved_by = await user_service.retrieve_one_by(
        db_session,
        filters=[V2User.email == payload.email],
    )
    assert isinstance(retrieved_by, V2UserResponseSchema)

    created_or_skip = await user_service.create_or_skip(
        db_session,
        {
            'id': uuid4(),
            'email': 'skip@ex.com',
            'name': 'Skip',
            'is_active': True,
        },
        conflict_columns=[V2User.email],
    )
    await db_session.commit()
    assert isinstance(created_or_skip, V2UserResponseSchema)

    duplicate = await user_service.create_or_skip(
        db_session,
        {
            'id': uuid4(),
            'email': created_or_skip.email,
            'name': 'Duplicate',
            'is_active': True,
        },
        conflict_columns=[V2User.email],
    )
    await db_session.commit()
    assert duplicate is None

    upserted = await user_service.upsert(
        db_session,
        {
            'id': uuid4(),
            'email': payload.email,
            'name': 'Upserted',
            'is_active': True,
        },
        conflict_columns=[V2User.email],
        update_only=['name'],
    )
    await db_session.commit()
    assert isinstance(upserted, V2UserResponseSchema)

    refreshed = await db_session.get(V2User, created.id)
    assert refreshed is not None
    assert refreshed.name == 'Upserted'

    deleted = await user_service.delete(db_session, created.id)
    await db_session.commit()

    assert isinstance(deleted, V2UserResponseSchema)
    assert deleted.id == created.id
    assert await db_session.get(V2User, created.id) is None

    with pytest.raises(NotFoundError):
        await user_service.retrieve(db_session, created.id)


async def test_service_bulk_create(
    db_session: AsyncSession,
    user_service: V2UserService,
) -> None:
    payloads = [
        _create_user_payload('bulk1@ex.com', 'Bulk1'),
        _create_user_payload('bulk2@ex.com', 'Bulk2'),
        _create_user_payload('bulk3@ex.com', 'Bulk3'),
    ]
    created = await user_service.bulk_create(db_session, payloads)
    await db_session.commit()

    assert len(created) == len(payloads)
    assert all(isinstance(item, V2UserResponseSchema) for item in created)
    assert {item.email for item in created} == {'bulk1@ex.com', 'bulk2@ex.com', 'bulk3@ex.com'}


async def test_service_bulk_create_raw(
    db_session: AsyncSession,
    user_service: V2UserService,
) -> None:
    payloads = [
        _create_user_payload('raw1@ex.com', 'Raw1'),
        _create_user_payload('raw2@ex.com', 'Raw2'),
    ]
    created = await user_service.bulk_create_raw(db_session, payloads)
    await db_session.commit()

    assert len(created) == len(payloads)
    assert all(isinstance(item, V2User) for item in created)


async def test_service_bulk_create_with_actor_id(
    db_session: AsyncSession,
    user_service: V2UserService,
) -> None:
    actor_id = uuid4()
    payloads = [
        _create_user_payload('actor1@ex.com', 'Actor1'),
        _create_user_payload('actor2@ex.com', 'Actor2'),
    ]
    created = await user_service.bulk_create(db_session, payloads, actor_id=actor_id)
    await db_session.commit()

    assert len(created) == len(payloads)
    assert all(item.updated_by == actor_id for item in created)


async def test_service_soft_delete_with_actor_id(
    db_session: AsyncSession,
    user_service: V2UserService,
) -> None:
    actor_id = uuid4()
    payload = _create_user_payload('soft-actor@ex.com', 'SoftActor')

    created = await user_service.create(db_session, payload)
    await db_session.commit()

    deleted = await user_service.soft_delete(db_session, created.id, actor_id=actor_id)
    await db_session.commit()

    assert isinstance(deleted, V2UserResponseSchema)
    assert deleted.updated_by == actor_id

    refreshed = await db_session.get(V2User, created.id)
    assert refreshed is not None
    assert refreshed.deleted_at is not None
    assert refreshed.updated_by == actor_id


async def test_service_soft_delete_by_with_actor_id(
    db_session: AsyncSession,
    user_service: V2UserService,
) -> None:
    actor_id = uuid4()
    payload = _create_user_payload('soft-by-actor@ex.com', 'SoftByActor')

    created = await user_service.create(db_session, payload)
    await db_session.commit()

    deleted = await user_service.soft_delete_by(
        db_session,
        filters=[V2User.id == created.id],
        actor_id=actor_id,
    )
    await db_session.commit()

    assert len(deleted) == 1
    assert isinstance(deleted[0], V2UserResponseSchema)
    assert deleted[0].updated_by == actor_id

    refreshed = await db_session.get(V2User, created.id)
    assert refreshed is not None
    assert refreshed.deleted_at is not None
    assert refreshed.updated_by == actor_id


async def test_service_soft_delete_without_actor_preserves_updated_by(
    db_session: AsyncSession,
    user_service: V2UserService,
) -> None:
    original_actor = uuid4()
    payload = _create_user_payload('soft-preserve@ex.com', 'SoftPreserve')

    created = await user_service.create(db_session, payload, actor_id=original_actor)
    await db_session.commit()
    assert created.updated_by == original_actor

    deleted = await user_service.soft_delete(db_session, created.id)
    await db_session.commit()

    assert isinstance(deleted, V2UserResponseSchema)
    assert deleted.updated_by == original_actor

    refreshed = await db_session.get(V2User, created.id)
    assert refreshed is not None
    assert refreshed.deleted_at is not None
    assert refreshed.updated_by == original_actor


async def test_service_bulk_create_duplicate_raises(
    db_session: AsyncSession,
    user_service: V2UserService,
) -> None:
    payload = _create_user_payload('dup@ex.com', 'Original')
    await user_service.create(db_session, payload)
    await db_session.commit()

    with pytest.raises(AlreadyExistsError):
        await user_service.bulk_create(
            db_session,
            [
                _create_user_payload('dup@ex.com', 'Duplicate'),
            ],
        )


async def test_service_soft_delete_raw(
    db_session: AsyncSession,
    user_service: V2UserService,
) -> None:
    payload = _create_user_payload('soft-raw@ex.com', 'SoftRaw')
    created = await user_service.create(db_session, payload)
    await db_session.commit()

    deleted = await user_service.soft_delete_raw(db_session, created.id)
    await db_session.commit()

    assert isinstance(deleted, V2User)
    assert deleted.id == created.id
    assert deleted.deleted_at is not None


async def test_service_delete_raw(
    db_session: AsyncSession,
    user_service: V2UserService,
) -> None:
    payload = _create_user_payload('del-raw@ex.com', 'DelRaw')
    created = await user_service.create(db_session, payload)
    await db_session.commit()

    deleted = await user_service.delete_raw(db_session, created.id)
    await db_session.commit()

    assert isinstance(deleted, V2User)
    assert deleted.id == created.id

    await db_session.invalidate()
    assert await db_session.get(V2User, created.id) is None


async def test_service_soft_delete_by_returns_list(
    db_session: AsyncSession,
    user_service: V2UserService,
) -> None:
    payloads = [
        _create_user_payload('sdel-by1@ex.com', 'SDelBy1'),
        _create_user_payload('sdel-by2@ex.com', 'SDelBy2'),
    ]
    for p in payloads:
        await user_service.create(db_session, p)
    await db_session.commit()

    deleted = await user_service.soft_delete_by(
        db_session,
        filters=[V2User.email.in_(['sdel-by1@ex.com', 'sdel-by2@ex.com'])],
    )
    await db_session.commit()

    assert len(deleted) == len(payloads)
    assert all(isinstance(d, V2UserResponseSchema) for d in deleted)
    assert {d.email for d in deleted} == {'sdel-by1@ex.com', 'sdel-by2@ex.com'}


async def test_service_soft_delete_by_empty_result(
    db_session: AsyncSession,
    user_service: V2UserService,
) -> None:
    deleted = await user_service.soft_delete_by(
        db_session,
        filters=[V2User.email == 'nonexistent@ex.com'],
    )
    assert deleted == []


async def test_service_delete_by_returns_list(
    db_session: AsyncSession,
    user_service: V2UserService,
) -> None:
    payloads = [
        _create_user_payload('del-by1@ex.com', 'DelBy1'),
        _create_user_payload('del-by2@ex.com', 'DelBy2'),
    ]
    for p in payloads:
        await user_service.create(db_session, p)
    await db_session.commit()

    deleted = await user_service.delete_by(
        db_session,
        filters=[V2User.email.in_(['del-by1@ex.com', 'del-by2@ex.com'])],
    )
    await db_session.commit()

    assert len(deleted) == len(payloads)
    assert all(isinstance(d, V2UserResponseSchema) for d in deleted)
