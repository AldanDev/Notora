from collections.abc import AsyncIterator, Iterator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer

from notora.v2.services.config import ServiceConfig
from tests.v2.test_integration.mocks.model import V2Profile, V2Role, V2User, V2UserRole
from tests.v2.test_integration.mocks.repo import (
    V2ProfileRepo,
    V2RoleRepo,
    V2UserRepo,
    V2UserRoleRepo,
)
from tests.v2.test_integration.mocks.schema import (
    V2ProfileResponseSchema,
    V2UserResponseSchema,
)
from tests.v2.test_integration.mocks.service import V2ProfileService, V2UserService


@pytest.fixture(scope='session')
def postgres_db(request) -> Iterator[PostgresContainer]:  # type: ignore[no-untyped-def]
    postgres_version = request.config.getoption('--postgres-version')
    with PostgresContainer(f'postgres:{postgres_version}') as db:
        yield db


@pytest.fixture(scope='session')
async def db_engine(postgres_db: PostgresContainer) -> AsyncIterator[AsyncEngine]:
    url = postgres_db.get_connection_url(driver='asyncpg')
    engine = create_async_engine(url)
    yield engine
    await engine.dispose()


@pytest.fixture(scope='session', autouse=True)
async def init_db(db_engine: AsyncEngine) -> None:
    async with db_engine.begin() as conn:
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS pgcrypto'))
        await conn.run_sync(V2User.metadata.create_all)
        stmt = text("SELECT c.relname FROM pg_class c WHERE c.relkind = 'S';")
        sequences = (await conn.execute(stmt)).scalars().all()
        for sequence in sequences:
            await conn.execute(text(f'ALTER SEQUENCE {sequence} RESTART;'))


@pytest.fixture(autouse=True)
async def clean_all_tables(db_engine: AsyncEngine) -> None:
    stmt = text("SELECT t.table_name FROM information_schema.tables t WHERE table_schema='public'")
    async with db_engine.begin() as conn:
        tables = (await conn.execute(stmt)).scalars().all()
        tables = [
            t_name
            for t_name in tables
            if not t_name.startswith('pg_')
            and not t_name.startswith('v_')
            and not t_name.startswith('alembic')
        ]
        for table_name in tables:
            await conn.execute(text(f'TRUNCATE TABLE "{table_name}" CASCADE;'))


@pytest.fixture(scope='session')
def session_factory(db_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(db_engine, expire_on_commit=False)


@pytest.fixture(scope='function')
async def db_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture(scope='function')
def user_repo() -> V2UserRepo:
    return V2UserRepo(V2User)


@pytest.fixture(scope='function')
def role_repo() -> V2RoleRepo:
    return V2RoleRepo(V2Role)


@pytest.fixture(scope='function')
def user_role_repo() -> V2UserRoleRepo:
    return V2UserRoleRepo(V2UserRole)


@pytest.fixture(scope='function')
def profile_repo() -> V2ProfileRepo:
    return V2ProfileRepo(V2Profile)


@pytest.fixture(scope='function')
def user_service(user_repo: V2UserRepo) -> V2UserService:
    config = ServiceConfig(
        detail_schema=V2UserResponseSchema,
        list_schema=V2UserResponseSchema,
    )
    return V2UserService(user_repo, config=config)


@pytest.fixture(scope='function')
def profile_service(profile_repo: V2ProfileRepo) -> V2ProfileService:
    config = ServiceConfig(detail_schema=V2ProfileResponseSchema)
    return V2ProfileService(profile_repo, config=config)
