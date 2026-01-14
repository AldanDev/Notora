from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from notora.v2.services.mixins.m2m import M2MSyncMode
from tests.v2.test_integration.mocks.model import V2Role, V2UserRole
from tests.v2.test_integration.mocks.schema import V2UserResponseSchema
from tests.v2.test_integration.mocks.service import V2UserService


async def _create_role(session: AsyncSession, name: str) -> V2Role:
    role = V2Role(id=uuid4(), name=name)
    session.add(role)
    await session.commit()
    return role


async def test_m2m_replace_on_update(
    db_session: AsyncSession,
    user_service: V2UserService,
) -> None:
    role_a = await _create_role(db_session, 'role-a')
    role_b = await _create_role(db_session, 'role-b')
    role_c = await _create_role(db_session, 'role-c')

    created = await user_service.create(
        db_session,
        {
            'id': uuid4(),
            'email': 'm2m@ex.com',
            'name': 'M2M',
            'is_active': True,
            'role_ids': [role_a.id, role_b.id],
        },
    )
    await db_session.commit()
    assert isinstance(created, V2UserResponseSchema)

    role_rows = (
        await db_session.scalars(select(V2UserRole).where(V2UserRole.user_id == created.id))
    ).all()
    assert {row.role_id for row in role_rows} == {role_a.id, role_b.id}

    await user_service.update(
        db_session,
        created.id,
        {
            'name': 'M2M Updated',
            'role_ids': [role_c.id],
        },
    )
    await db_session.commit()

    updated_rows = (
        await db_session.scalars(select(V2UserRole).where(V2UserRole.user_id == created.id))
    ).all()
    assert {row.role_id for row in updated_rows} == {role_c.id}


async def test_m2m_add_mode(
    db_session: AsyncSession,
    user_service: V2UserService,
) -> None:
    role_a = await _create_role(db_session, 'add-a')
    role_b = await _create_role(db_session, 'add-b')

    user_service.m2m_sync_mode = M2MSyncMode.ADD
    created = await user_service.create(
        db_session,
        {
            'id': uuid4(),
            'email': 'add@ex.com',
            'name': 'Add',
            'is_active': True,
            'role_ids': [role_a.id],
        },
    )
    await db_session.commit()
    assert isinstance(created, V2UserResponseSchema)

    await user_service.update(
        db_session,
        created.id,
        {
            'name': 'Add Updated',
            'role_ids': [role_a.id, role_b.id],
        },
    )
    await db_session.commit()

    rows = (
        await db_session.scalars(select(V2UserRole).where(V2UserRole.user_id == created.id))
    ).all()
    assert {row.role_id for row in rows} == {role_a.id, role_b.id}
