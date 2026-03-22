import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.database_layer.database import get_db
from app.database_layer.models import Base
from app.main import app

# 1. Use an in-memory DB for tests (Fast & Clean)
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def test_db_session():
    """
    Creates a fresh database for every single test function.
    """
    # Create Engine
    engine = create_async_engine(TEST_DB_URL, echo=False)
    
    # Create Tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create Session Factory
    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    async with SessionLocal() as session:
        yield session
    
    # Cleanup (Drop tables)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client(test_db_session):
    """
    A fake browser (HTTP Client) that calls our API.
    It overrides the 'get_db' dependency to use our TEST DB instead of the real one.
    """
    
    # Dependency Override: Force app to use test_db_session
    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db
    
    # Create the Async Client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    # Cleanup overrides
    app.dependency_overrides.clear()