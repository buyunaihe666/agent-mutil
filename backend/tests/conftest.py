"""Shared pytest fixtures for backend tests."""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings, get_settings
from app.main import create_app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        APP_ENV="testing",
        DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/test_db",
        REDIS_URL="redis://localhost:6379/1",
        LLM_API_KEYS="{}",
        ENCRYPTION_KEY="test-key-0123456789abcdef0123456789abcdef",
        CORS_ORIGINS="*",
    )


@pytest_asyncio.fixture
async def app(test_settings: Settings):
    application = create_app()
    application.dependency_overrides[get_settings] = lambda: test_settings
    return application


@pytest_asyncio.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
