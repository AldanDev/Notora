from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from notora.v2.exceptions.common import NotFoundError
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

    await user_service.soft_delete(db_session, created.id)
    await db_session.commit()

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

    await user_service.delete(db_session, created.id)
    await db_session.commit()
    assert await db_session.get(V2User, created.id) is None

    with pytest.raises(NotFoundError):
        await user_service.retrieve(db_session, created.id)
