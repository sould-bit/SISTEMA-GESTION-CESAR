
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.database import get_session
from app.main import app
from app.models import Company, Category, User, Product
from app.utils.security import get_password_hash, create_access_token
from decimal import Decimal
import uuid
import os

# Import Redis Mock Fixture
from tests.fixtures.redis_mock import mock_redis

# Use environment variable or fallback to Docker DB
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/cesar_db")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# NOTE: event_loop fixture removed to avoid conflict with pytest-asyncio 0.24+
# when asyncio_default_fixture_loop_scope = session is set in pytest.ini

@pytest.fixture(scope="session")
async def init_db():
    try:
        # Check dialect
        is_postgres = engine.url.drivername == 'postgresql+asyncpg'

        async with engine.begin() as conn:
            if is_postgres:
                from sqlalchemy import text
                # CASCADE drop for Postgres to handle foreign keys
                await conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
            else:
                # Standard drop for SQLite
                await conn.run_sync(SQLModel.metadata.drop_all)

            # Create all tables
            await conn.run_sync(SQLModel.metadata.create_all)
    except Exception as e:
        print(f"Error initializing DB: {e}")
        raise e
    yield

@pytest.fixture
async def session(init_db) -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    # Override the dependency
    def get_session_override():
        return session

    # If app is wrapped in socketio.ASGIApp, we need to access the inner FastAPI app
    fastapi_app = app
    if hasattr(app, "other_asgi_app"):
        fastapi_app = app.other_asgi_app

    fastapi_app.dependency_overrides[get_session] = get_session_override
    
    # httpx AsyncClient accepts 'app' or 'transport'
    # 'transport' is usually preferred for ASGI apps
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    fastapi_app.dependency_overrides.clear()

@pytest.fixture
async def test_client(client):
    yield client

@pytest.fixture
def db_session(session):
    return session

@pytest.fixture
async def test_company(session: AsyncSession):
    uid = uuid.uuid4().hex[:8]
    company = Company(name=f"Recipe Test Corp {uid}", slug=f"recipe-corp-{uid}")
    session.add(company)
    await session.commit()
    await session.refresh(company)
    return company

@pytest.fixture
async def test_category(session: AsyncSession, test_company: Company):
    uid = uuid.uuid4().hex[:8]
    category = Category(name=f"Test Category {uid}", company_id=test_company.id)
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category

@pytest.fixture
async def test_user(session: AsyncSession, test_company: Company):
    uid = uuid.uuid4().hex[:8]
    hashed_password = get_password_hash("testpassword")
    user = User(
        username=f"user_{uid}",
        email=f"user_{uid}@example.com",
        hashed_password=hashed_password,
        company_id=test_company.id,
        is_active=True,
        role="admin"
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

@pytest.fixture
async def user_token(test_user: User, test_company: Company):
    # Create valid token for testing
    data = {
        "sub": test_user.email,
        "company_slug": test_company.slug,
        "role": test_user.role,
        "user_id": str(test_user.id)
    }
    return create_access_token(data=data)

@pytest.fixture
async def test_product(session: AsyncSession, test_company: Company, test_category: Category):
    uid = uuid.uuid4().hex[:8]
    product = Product(
        name=f"Test Product {uid}",
        price=Decimal("10.00"),
        company_id=test_company.id,
        category_id=test_category.id,
        is_active=True,
        stock=Decimal("100.0")
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product

@pytest.fixture
async def test_products_batch(session: AsyncSession, test_company: Company, test_category: Category):
    products = []
    for i in range(5):
        uid = uuid.uuid4().hex[:8]
        product = Product(
            name=f"Product {i} {uid}",
            price=Decimal("10.00"),
            company_id=test_company.id,
            category_id=test_category.id,
            is_active=True,
            stock=Decimal("100.0")
        )
        session.add(product)
        products.append(product)
    await session.commit()
    for p in products:
        await session.refresh(p)
    return products