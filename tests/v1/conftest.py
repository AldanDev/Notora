import os
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

from tests.v1.test_integration.mocks.model import MockModel
from tests.v1.test_integration.mocks.repo import MockRepo
from tests.v1.test_integration.mocks.schema import MockModelResponseSchema
from tests.v1.test_integration.mocks.service import MockService

DB_DSN = os.getenv(
    'DB_DSN',
    'postgresql+asyncpg://notora:notora@tests_db:5432/notora',
)


@pytest.fixture(scope='session')
def postgres_db() -> Iterator[PostgresContainer]:
    with PostgresContainer() as db:
        yield db


@pytest.fixture(scope='session')
async def db_engine(postgres_db: PostgresContainer) -> AsyncIterator[AsyncEngine]:
    url = postgres_db.get_connection_url(driver='asyncpg')
    engine = create_async_engine(url)
    yield engine
    await engine.dispose()


@pytest.fixture(scope='session', autouse=True)
async def init_db(db_engine: AsyncEngine) -> None:
    """Restart all sequences from database.

    Called one time for all tests.
    Cleans up "global_id_sequence" in addition to table sequences,
    so just TRUNCATE TABLE ... RESTART IDENTITY CASCADE wouldn't be enough.
    """
    async with db_engine.begin() as conn:
        await conn.run_sync(MockModel.metadata.create_all)
        stmt = text("SELECT c.relname FROM pg_class c WHERE c.relkind = 'S';")
        sequences = (await conn.execute(stmt)).scalars().all()
        for sequence in sequences:
            await conn.execute(text(f'ALTER SEQUENCE {sequence} RESTART;'))


@pytest.fixture(autouse=True)
async def clean_all_tables(db_engine: AsyncEngine) -> None:
    """Clean all tables before tests and after every test."""
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
    db_engine: AsyncEngine,
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture(scope='function')
def mock_repo() -> MockRepo:
    return MockRepo(MockModel)


@pytest.fixture(scope='function')
def mock_service(mock_repo: MockRepo) -> MockService:
    service = MockService(mock_repo)
    service.response_schema = MockModelResponseSchema
    return service
