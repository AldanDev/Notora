from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from notora.v2.repositories.params import PaginationParams, QueryParams
from tests.v2.test_integration.mocks.model import V2User
from tests.v2.test_integration.mocks.schema import V2UserCreateSchema
from tests.v2.test_integration.mocks.service import V2UserService


def _payload(email: str, name: str) -> V2UserCreateSchema:
    return V2UserCreateSchema(id=uuid4(), email=email, name=name, is_active=True)


async def _seed_one_live_one_deleted(
    db_session: AsyncSession,
    user_service: V2UserService,
) -> None:
    live = await user_service.create(db_session, _payload('live@ex.com', 'Live'))
    deleted = await user_service.create(db_session, _payload('deleted@ex.com', 'Deleted'))
    await user_service.soft_delete(db_session, deleted.id)
    await db_session.commit()
    _ = live


async def test_list_params_excludes_soft_deleted_by_default(
    db_session: AsyncSession,
    user_service: V2UserService,
) -> None:
    await _seed_one_live_one_deleted(db_session, user_service)

    items = await user_service.list_params(db_session, QueryParams[V2User](limit=None))
    emails = {item.email for item in items}
    assert emails == {'live@ex.com'}


async def test_list_params_includes_soft_deleted_when_bypassed(
    db_session: AsyncSession,
    user_service: V2UserService,
) -> None:
    await _seed_one_live_one_deleted(db_session, user_service)

    items = await user_service.list_params(
        db_session,
        QueryParams[V2User](limit=None, apply_default_filters=False),
    )
    emails = {item.email for item in items}
    assert emails == {'live@ex.com', 'deleted@ex.com'}


async def test_paginate_excludes_soft_deleted_by_default(
    db_session: AsyncSession,
    user_service: V2UserService,
) -> None:
    await _seed_one_live_one_deleted(db_session, user_service)

    page = await user_service.paginate(db_session, limit=20, offset=0)
    assert page.meta.total == 1


async def test_paginate_includes_soft_deleted_when_bypassed(
    db_session: AsyncSession,
    user_service: V2UserService,
) -> None:
    await _seed_one_live_one_deleted(db_session, user_service)

    page = await user_service.paginate(db_session, limit=20, offset=0, apply_default_filters=False)
    expected_total_including_deleted = 2
    assert page.meta.total == expected_total_including_deleted


async def test_paginate_params_propagates_bypass(
    db_session: AsyncSession,
    user_service: V2UserService,
) -> None:
    await _seed_one_live_one_deleted(db_session, user_service)

    page = await user_service.paginate_params(
        db_session,
        PaginationParams[V2User](limit=20, offset=0, apply_default_filters=False),
    )
    expected_total_including_deleted = 2
    assert page.meta.total == expected_total_including_deleted
