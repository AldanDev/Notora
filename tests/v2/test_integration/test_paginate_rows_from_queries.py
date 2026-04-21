from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from notora.v2.schemas.base import BaseResponseSchema
from tests.v2.test_integration.mocks.model import V2Role, V2User, V2UserRole
from tests.v2.test_integration.mocks.schema import V2UserCreateSchema
from tests.v2.test_integration.mocks.service import V2UserService


class UserWithRoleCountSchema(BaseResponseSchema):
    id: UUID
    email: str
    name: str
    role_count: int


async def _seed_users_with_roles(db_session: AsyncSession, user_service: V2UserService) -> None:
    u1 = await user_service.create(
        db_session,
        V2UserCreateSchema(id=uuid4(), email='u1@ex.com', name='U1', is_active=True),
    )
    u2 = await user_service.create(
        db_session,
        V2UserCreateSchema(id=uuid4(), email='u2@ex.com', name='U2', is_active=True),
    )
    await user_service.create(
        db_session,
        V2UserCreateSchema(id=uuid4(), email='u3@ex.com', name='U3', is_active=True),
    )
    role_a = V2Role(id=uuid4(), name='A')
    role_b = V2Role(id=uuid4(), name='B')
    db_session.add_all([role_a, role_b])
    await db_session.flush()
    db_session.add_all([
        V2UserRole(id=uuid4(), user_id=u1.id, role_id=role_a.id),
        V2UserRole(id=uuid4(), user_id=u1.id, role_id=role_b.id),
        V2UserRole(id=uuid4(), user_id=u2.id, role_id=role_a.id),
    ])
    await db_session.commit()


async def test_paginate_rows_from_queries_returns_enriched_schema(
    db_session: AsyncSession,
    user_service: V2UserService,
) -> None:
    await _seed_users_with_roles(db_session, user_service)

    role_count_subq = (
        select(func.count())
        .select_from(V2UserRole)
        .where(V2UserRole.user_id == V2User.id)
        .correlate(V2User)
        .scalar_subquery()
    )

    limit = 2
    offset = 0
    data_query = (
        select(V2User, role_count_subq.label('role_count'))
        .where(V2User.deleted_at.is_(None))
        .order_by(V2User.email.asc())
        .limit(limit)
        .offset(offset)
    )
    count_query = select(func.count()).select_from(V2User).where(V2User.deleted_at.is_(None))

    def to_schema(row: Any) -> UserWithRoleCountSchema:
        user: V2User = row[0]
        role_count: int = row[1]
        return UserWithRoleCountSchema(
            id=user.id, email=user.email, name=user.name, role_count=role_count,
        )

    page = await user_service.paginate_rows_from_queries(
        db_session,
        data_query=data_query,
        count_query=count_query,
        row_to_schema=to_schema,
        limit=limit,
        offset=offset,
    )

    expected_total = 3
    expected_page_size = 2
    assert page.meta.total == expected_total
    assert page.meta.limit == limit
    assert page.meta.offset == offset
    assert len(page.data) == expected_page_size
    expected_by_email = {'u1@ex.com': 2, 'u2@ex.com': 1}
    by_email = {item.email: item.role_count for item in page.data}
    assert by_email == expected_by_email
