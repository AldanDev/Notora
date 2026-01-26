from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from tests.v2.test_integration.mocks.model import V2User
from tests.v2.test_integration.mocks.repo import V2UserRepo


async def _create_user(
    session: AsyncSession,
    repo: V2UserRepo,
    *,
    email: str,
    name: str,
    is_active: bool = True,
) -> V2User:
    payload = {
        'id': uuid4(),
        'email': email,
        'name': name,
        'is_active': is_active,
    }
    user = (await session.scalars(repo.create(payload))).one()
    await session.commit()
    return user


async def _seed_users(session: AsyncSession) -> list[V2User]:
    users = [
        V2User(id=uuid4(), email='a@ex.com', name='Alice', is_active=True),
        V2User(id=uuid4(), email='b@ex.com', name='Bob', is_active=False),
        V2User(id=uuid4(), email='c@ex.com', name='Cara', is_active=True),
    ]
    session.add_all(users)
    await session.commit()
    return users


async def test_repo_create_retrieve_and_count(
    db_session: AsyncSession,
    user_repo: V2UserRepo,
) -> None:
    user = await _create_user(
        db_session,
        user_repo,
        email='one@ex.com',
        name='One',
    )

    query = user_repo.retrieve(user.id)
    retrieved = (await db_session.scalars(query)).one()
    assert retrieved.id == user.id

    total = (await db_session.execute(user_repo.count())).scalar_one()
    assert total == 1


async def test_repo_list_filters_and_ordering(
    db_session: AsyncSession,
    user_repo: V2UserRepo,
) -> None:
    await _seed_users(db_session)

    query = user_repo.list(
        filters=[V2User.is_active.is_(True)],
        ordering=[V2User.email.desc()],
        limit=None,
    )
    users = (await db_session.scalars(query)).all()

    assert [user.email for user in users] == ['c@ex.com', 'a@ex.com']


async def test_repo_update_and_delete(
    db_session: AsyncSession,
    user_repo: V2UserRepo,
) -> None:
    user = await _create_user(
        db_session,
        user_repo,
        email='update@ex.com',
        name='Before',
    )

    await db_session.execute(user_repo.update(user.id, {'name': 'After'}))
    await db_session.commit()

    refreshed = await db_session.get(V2User, user.id)
    assert refreshed is not None
    assert refreshed.name == 'After'

    await db_session.execute(user_repo.delete(user.id))
    await db_session.commit()

    assert await db_session.get(V2User, user.id) is None


async def test_repo_delete_by(
    db_session: AsyncSession,
    user_repo: V2UserRepo,
) -> None:
    users = await _seed_users(db_session)
    delete_query = user_repo.delete_by(
        filters=[V2User.email.in_([users[0].email, users[1].email])]
    )
    await db_session.execute(delete_query)
    await db_session.commit()

    remaining = (await db_session.scalars(user_repo.list(limit=None))).all()
    assert [user.email for user in remaining] == [users[2].email]


async def test_repo_soft_delete(
    db_session: AsyncSession,
    user_repo: V2UserRepo,
) -> None:
    user = await _create_user(
        db_session,
        user_repo,
        email='soft@ex.com',
        name='Soft',
    )

    await db_session.execute(user_repo.soft_delete(user.id))
    await db_session.commit()

    refreshed = await db_session.get(V2User, user.id)
    assert refreshed is not None
    assert refreshed.deleted_at is not None

    listed = (await db_session.scalars(user_repo.list(limit=None))).all()
    assert listed == []


async def test_repo_create_or_skip(
    db_session: AsyncSession,
    user_repo: V2UserRepo,
) -> None:
    payload = {'id': uuid4(), 'email': 'skip@ex.com', 'name': 'Skip', 'is_active': True}

    create_query = user_repo.create_or_skip(payload, conflict_columns=[V2User.email])
    created = (await db_session.scalars(create_query)).one_or_none()
    await db_session.commit()
    assert created is not None

    duplicate_payload = {**payload, 'id': uuid4()}
    duplicate_query = user_repo.create_or_skip(
        duplicate_payload,
        conflict_columns=[V2User.email],
    )
    duplicate = (await db_session.scalars(duplicate_query)).one_or_none()
    await db_session.commit()
    assert duplicate is None


async def test_repo_upsert_updates_existing(
    db_session: AsyncSession,
    user_repo: V2UserRepo,
) -> None:
    payload = {'id': uuid4(), 'email': 'upsert@ex.com', 'name': 'Before', 'is_active': True}
    user = (await db_session.scalars(user_repo.create(payload))).one()
    await db_session.commit()

    upsert_payload = {
        'id': uuid4(),
        'email': user.email,
        'name': 'After',
        'is_active': True,
    }
    upsert_query = user_repo.upsert(
        upsert_payload,
        conflict_columns=[V2User.email],
        update_only=['name'],
    )
    updated = (await db_session.scalars(upsert_query)).one()
    await db_session.commit()

    assert updated.id == user.id
    refreshed = await db_session.get(V2User, user.id)
    assert refreshed is not None
    await db_session.refresh(refreshed)
    assert refreshed.name == 'After'
