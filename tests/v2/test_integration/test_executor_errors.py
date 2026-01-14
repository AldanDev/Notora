from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from notora.v2.exceptions.common import AlreadyExistsError, FKNotFoundError
from tests.v2.test_integration.mocks.service import V2ProfileService, V2UserService


async def test_unique_violation_translates(
    db_session: AsyncSession,
    user_service: V2UserService,
) -> None:
    payload = {
        'id': uuid4(),
        'email': 'unique@ex.com',
        'name': 'Unique',
        'is_active': True,
    }
    await user_service.create(db_session, payload)
    await db_session.commit()

    duplicate_payload = {
        'id': uuid4(),
        'email': 'unique@ex.com',
        'name': 'Duplicate',
        'is_active': True,
    }
    with pytest.raises(AlreadyExistsError):
        await user_service.create(db_session, duplicate_payload)


async def test_fk_violation_translates(
    db_session: AsyncSession,
    profile_service: V2ProfileService,
) -> None:
    payload = {
        'id': uuid4(),
        'user_id': uuid4(),
        'bio': 'profile',
    }

    with pytest.raises(FKNotFoundError) as exc:
        await profile_service.create(db_session, payload)

    assert exc.value.table_name == 'v2_profile'
