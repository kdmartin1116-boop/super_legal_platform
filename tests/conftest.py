# Test Configuration
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from backend.app import app
from backend.modules.database_enhanced import Base


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db():
    """Create test database"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    yield async_session
    
    await engine.dispose()


@pytest.fixture
async def client():
    """Test client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client