from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from uuid import uuid4

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Connection
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import db_modules  # noqa: F401
from auth.models import UserInfoDTO
from auth.orm import User
from config.dependencies import get_authenticated_user
from database import Base
from main import app, container
from setting.orm import CalorieSetting
from tests.fakes import FakeOpenAI

TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@postgres-test:5432/main_be_test"
)


@pytest_asyncio.fixture
async def engine() -> AsyncGenerator[AsyncEngine]:
    engine = create_async_engine(TEST_DATABASE_URL)
    try:
        yield engine
    finally:
        await engine.dispose()


def drop_all_tables(conn: Connection) -> None:
    Base.metadata.drop_all(bind=conn)


def create_all_tables(conn: Connection) -> None:
    Base.metadata.create_all(bind=conn)


@pytest_asyncio.fixture
async def db(
    engine: AsyncEngine,
) -> AsyncGenerator[async_sessionmaker[AsyncSession]]:
    async with engine.begin() as conn:
        await conn.run_sync(drop_all_tables)
        await conn.run_sync(create_all_tables)

    session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    container.async_session_maker.override(session_maker)
    container.openai_client.override(lambda: FakeOpenAI())

    try:
        yield session_maker
    finally:
        container.async_session_maker.reset_override()
        async with engine.begin() as conn:
            await conn.run_sync(drop_all_tables)


@pytest_asyncio.fixture
async def client(
    db: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def authenticated_user(
    db: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[UserInfoDTO]:
    user = User(
        id=uuid4(),
        username="test-user",
        email="test-user@example.com",
        hashed_password="not-used",
        is_verified=True,
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )

    async with db() as session:
        session.add(user)
        await session.commit()

    user_info = UserInfoDTO.model_validate(user)

    async def override_get_authenticated_user() -> UserInfoDTO:
        return user_info

    app.dependency_overrides[get_authenticated_user] = override_get_authenticated_user

    try:
        yield user_info
    finally:
        app.dependency_overrides.pop(get_authenticated_user, None)


@pytest_asyncio.fixture
async def calorie_setting(
    db: async_sessionmaker[AsyncSession],
    authenticated_user: UserInfoDTO,
) -> CalorieSetting:
    setting = CalorieSetting(user_id=authenticated_user.id)
    async with db() as session:
        session.add(setting)
        await session.commit()
    return setting
