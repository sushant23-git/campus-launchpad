import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database.base_model import Base
from app.core.config import settings

TEST_DATABASE_URL = settings.DATABASE_URL.replace("campus_launchpad", "campus_launchpad_test")

@pytest.fixture(scope="session")
def event_loop():
    """Create session-wide event loop for running async tests."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Setup test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create tables in test database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide isolated transaction session for each test execution."""
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
        # Rollback everything to keep tests isolated
        await session.rollback()
