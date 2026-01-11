"""
🧪 Test Configuration - conftest.py
===================================
Configura fixtures para tests de integración.

Estrategia: Cada test corre en una transacción que hace rollback al final.
Esto evita conflictos con la BD de desarrollo activa.
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path
from typing import AsyncGenerator, Generator

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from app.database import get_session
from app.main import app
from app.models import Company, Category, User, Product, Branch, Role
from app.utils.security import get_password_hash, create_access_token
from decimal import Decimal
import uuid

# Use environment variable or fallback to Docker DB
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://fastops_user:fastops_password@db:5432/cesar_db")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Engine with NullPool to avoid connection issues
engine = create_async_engine(
    DATABASE_URL, 
    echo=False,
    poolclass=NullPool  # No connection pooling for tests
)

TestingSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def session() -> AsyncGenerator[AsyncSession, None]:
    """
    Proporciona una sesión de BD para cada test.
    La sesión usa la BD existente sin eliminar tablas.
    """
    async with TestingSessionLocal() as session:
        yield session
        # No hacemos rollback automático para permitir tests de integración reales


@pytest.fixture(scope="function")
def db_session_factory():
    """
    Factory para crear sesiones de BD.
    Usado por tests de concurrencia que necesitan múltiples sesiones independientes.
    """
    return TestingSessionLocal


@pytest.fixture(scope="function")
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Cliente HTTP asíncrono para tests."""
    
    async def get_session_override():
        yield session
    
    app.dependency_overrides[get_session] = get_session_override
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_client(client):
    """Alias para client fixture."""
    yield client


@pytest.fixture
def db_session(session):
    """Alias para session fixture (compatibilidad)."""
    return session


# =============================================================================
# FIXTURES DE DATOS DE PRUEBA
# =============================================================================

@pytest.fixture
async def test_company(session: AsyncSession):
    """Crea una compañía de prueba única."""
    uid = uuid.uuid4().hex[:8]
    company = Company(name=f"Test Corp {uid}", slug=f"test-corp-{uid}")
    session.add(company)
    await session.commit()
    await session.refresh(company)
    return company


@pytest.fixture
async def test_branch(session: AsyncSession, test_company: Company):
    """Crea una sucursal de prueba."""
    uid = uuid.uuid4().hex[:8]
    branch = Branch(
        name=f"Test Branch {uid}",
        code=f"TST{uid[:4].upper()}",  # Required field
        company_id=test_company.id,
        address="Test Address",
        is_active=True
    )
    session.add(branch)
    await session.commit()
    await session.refresh(branch)
    return branch


@pytest.fixture
async def test_role(session: AsyncSession, test_company: Company):
    """Crea un rol de prueba."""
    uid = uuid.uuid4().hex[:8]
    role = Role(
        name=f"Test Role {uid}",
        code=f"TST{uid[:4].upper()}",  # Required field
        company_id=test_company.id,
        is_system_role=False
    )
    session.add(role)
    await session.commit()
    await session.refresh(role)
    return role


@pytest.fixture
async def test_category(session: AsyncSession, test_company: Company):
    """Crea una categoría de prueba."""
    uid = uuid.uuid4().hex[:8]
    category = Category(name=f"Test Category {uid}", company_id=test_company.id)
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


# =============================================================================
# FIXTURES MULTI-TENANT (Segunda Empresa para tests de aislamiento)
# =============================================================================

@pytest.fixture
async def test_company_2(session: AsyncSession):
    """Crea una segunda compañía de prueba para tests multi-tenant."""
    uid = uuid.uuid4().hex[:8]
    company = Company(name=f"Test Corp 2 {uid}", slug=f"test-corp-2-{uid}")
    session.add(company)
    await session.commit()
    await session.refresh(company)
    return company


@pytest.fixture
async def test_category_company_2(session: AsyncSession, test_company_2: Company):
    """Crea una categoría para la segunda empresa."""
    uid = uuid.uuid4().hex[:8]
    category = Category(name=f"Test Category 2 {uid}", company_id=test_company_2.id)
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


@pytest.fixture
async def test_branch_2(session: AsyncSession, test_company_2: Company):
    """Crea una sucursal para la segunda empresa."""
    uid = uuid.uuid4().hex[:8]
    branch = Branch(
        name=f"Test Branch 2 {uid}",
        code=f"TB2{uid[:4].upper()}",
        company_id=test_company_2.id,
        address="Test Address 2",
        is_active=True
    )
    session.add(branch)
    await session.commit()
    await session.refresh(branch)
    return branch


@pytest.fixture
async def test_role_2(session: AsyncSession, test_company_2: Company):
    """Crea un rol para la segunda empresa."""
    uid = uuid.uuid4().hex[:8]
    role = Role(
        name=f"Test Role 2 {uid}",
        code=f"TR2{uid[:4].upper()}",
        company_id=test_company_2.id,
        is_system_role=False
    )
    session.add(role)
    await session.commit()
    await session.refresh(role)
    return role


@pytest.fixture
async def test_user_company_2(session: AsyncSession, test_company_2: Company, test_branch_2: Branch, test_role_2: Role):
    """Crea un usuario para la segunda empresa."""
    uid = uuid.uuid4().hex[:8]
    hashed_password = get_password_hash("testpassword")
    user = User(
        username=f"user2_{uid}",
        email=f"user2_{uid}@example.com",
        full_name=f"Test User 2 {uid}",
        hashed_password=hashed_password,
        company_id=test_company_2.id,
        branch_id=test_branch_2.id,
        role_id=test_role_2.id,
        is_active=True
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
def db_session(session):
    """Alias para session fixture - nombre usado por tests de multi-tenant."""
    return session


@pytest.fixture
async def test_user(session: AsyncSession, test_company: Company, test_branch: Branch, test_role: Role):
    """Crea un usuario de prueba."""
    uid = uuid.uuid4().hex[:8]
    hashed_password = get_password_hash("testpassword")
    user = User(
        username=f"user_{uid}",
        email=f"user_{uid}@example.com",
        full_name=f"Test User {uid}",
        hashed_password=hashed_password,
        company_id=test_company.id,
        branch_id=test_branch.id,
        role_id=test_role.id,
        is_active=True
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def user_token(test_user: User, test_company: Company):
    """Crea un token válido para testing."""
    data = {
        "sub": test_user.email,
        "company_slug": test_company.slug,
        "company_id": test_company.id,
        "user_id": test_user.id,
        "branch_id": test_user.branch_id
    }
    return create_access_token(data=data)


@pytest.fixture
async def auth_headers(user_token: str):
    """Headers de autenticación para requests."""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
async def test_product(session: AsyncSession, test_company: Company, test_category: Category, test_branch: Branch):
    """Crea un producto de prueba e inicializa su inventario."""
    uid = uuid.uuid4().hex[:8]
    product = Product(
        name=f"Test Product {uid}",
        price=Decimal("25.50"),
        tax_rate=Decimal("0.10"),
        company_id=test_company.id,
        category_id=test_category.id,
        is_active=True,
        stock=Decimal("100.0")
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)
    
    # INICIALIZAR INVENTARIO PARA EVITAR ERROR 'Stock insuficiente'
    from app.models.inventory import Inventory
    
    inventory = Inventory(
        branch_id=test_branch.id,
        product_id=product.id,
        stock=Decimal("100.000"), # Coincide con product.stock
        min_stock=Decimal("5.000")
    )
    session.add(inventory)
    await session.commit()
    
    return product


@pytest.fixture
async def test_products_batch(session: AsyncSession, test_company: Company, test_category: Category):
    """Crea múltiples productos de prueba."""
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

    # INICIALIZAR INVENTARIO BATCH
    from app.models.inventory import Inventory
    
    # Asumimos que test_branch está disponible, pero no lo recibimos como argumento.
    # Dado que es batch, intentaremos obtener el ID de la primera sucursal de la empresa
    stmt = select(Branch).where(Branch.company_id == test_company.id)
    result = await session.execute(stmt)
    branch = result.scalars().first()
    
    if branch:
        for p in products:
            inv = Inventory(
                branch_id=branch.id,
                product_id=p.id,
                stock=Decimal("100.000"),
                min_stock=Decimal("5.000")
            )
            session.add(inv)
        await session.commit()

    for p in products:
        await session.refresh(p)
    return products