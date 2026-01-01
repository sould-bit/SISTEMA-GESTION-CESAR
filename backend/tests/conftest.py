"""
Configuración global de pruebas para el sistema RBAC.

Este archivo contiene fixtures y configuraciones compartidas
para todas las pruebas del sistema.
"""

import asyncio
import pytest
import pytest_asyncio
import logging
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool, NullPool
from sqlmodel import SQLModel

# Importar todos los modelos para que SQLModel los registre en metadata
from app.models import User, Company, Product, Category, Role, Permission, RolePermission, Branch

import os

# Configuración de base de datos para pruebas
# Si estamos en el entorno Docker, preferimos PostgreSQL para pruebas de concurrencia reales
DEFAULT_TEST_DB = "sqlite+aiosqlite:///:memory:"
DATABASE_URL = os.getenv("DATABASE_URL")
USE_POSTGRES = os.getenv("USE_REAL_DB", "false").lower() == "true"

# Ajustar driver para async si es PostgreSQL
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

TEST_DATABASE_URL = DATABASE_URL if USE_POSTGRES and DATABASE_URL else DEFAULT_TEST_DB

# Engine de pruebas (lazy initialization)
test_engine = None
TestSessionLocal = None

def get_test_engine():
    """Obtener engine de pruebas (lazy loading)."""
    global test_engine, TestSessionLocal
    if test_engine is None:
        connect_args = {"timeout": 30}
        
        # SQLite específico
        if TEST_DATABASE_URL.startswith("sqlite"):
            connect_args["check_same_thread"] = False
            poolclass = StaticPool
        else:
            # PostgreSQL: Usar NullPool para evitar compartir conexiones en tests concurrentes
            # y evitar errores de 'another operation is in progress'
            connect_args = {}
            poolclass = NullPool

        test_engine = create_async_engine(
            TEST_DATABASE_URL,
            connect_args=connect_args,
            poolclass=poolclass,
            echo=False,
        )
        TestSessionLocal = async_sessionmaker(
            bind=test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return test_engine, TestSessionLocal


@pytest.fixture(scope="session")
def event_loop():
    """Crear una instancia del event loop para toda la sesión de pruebas."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()





@pytest_asyncio.fixture(scope="session")
async def setup_database():
    """Configurar base de datos para pruebas."""
    engine, _ = get_test_engine()
    # Crear todas las tablas
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield

    # Limpiar después de las pruebas (SOLO en SQLite para evitar borrar DB real)
    if not USE_POSTGRES:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
    else:
        logger = logging.getLogger(__name__)
        logger.info("ℹ️ Manteniendo base de datos PostgreSQL activa después de los tests.")


@pytest_asyncio.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Fixture que proporciona una sesión de base de datos limpia."""
    _, session_maker = get_test_engine()
    async with session_maker() as session:
        # Limpiar datos entre pruebas
        await session.begin()

        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture
def db_session_factory(setup_database):
    """Fixture que proporciona un factory para crear sesiones de base de datos."""
    _, session_maker = get_test_engine()
    return session_maker


@pytest.fixture
def mock_redis():
    """Mock de Redis para pruebas."""
    class MockRedis:
        def __init__(self):
            self.data = {}

        async def get(self, key):
            return self.data.get(key)

        async def setex(self, key, ttl, value):
            self.data[key] = value
            return True

        async def delete(self, *keys):
            for key in keys:
                self.data.pop(key, None)
            return len(keys)

        async def keys(self, pattern):
            # Implementación simple del patrón
            return [k for k in self.data.keys() if pattern.replace("*", "") in k]

    return MockRedis()


# Fixture para crear datos de prueba comunes
@pytest_asyncio.fixture
async def test_company(db_session: AsyncSession):
    """Crear una compañía de prueba con identificadores únicos."""
    from app.models import Company
    from uuid import uuid4

    # Usar UUID para evitar conflictos con datos existentes
    unique_id = str(uuid4())[:8]

    company = Company(
        name=f"Empresa Test {unique_id}",
        slug=f"test-company-{unique_id}",
        email=f"test-{unique_id}@empresa.com",
        phone="+1234567890",
        address="Dirección de prueba",
        is_active=True
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)
    return company


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, test_company):
    """Crear un usuario de prueba con identificadores únicos."""
    from app.models import User
    from app.utils.security import get_password_hash
    from uuid import uuid4

    unique_id = str(uuid4())[:8]
    user = User(
        username=f"testuser-{unique_id}",
        email=f"test-{unique_id}@example.com",
        full_name="Usuario de Prueba",
        hashed_password=get_password_hash("testpass123"),
        company_id=test_company.id,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_permission_category(db_session: AsyncSession, test_company):
    """Crear una categoría de permisos de prueba con identificadores únicos."""
    from app.models import PermissionCategory
    from uuid import uuid4

    unique_id = str(uuid4())[:8]
    category = PermissionCategory(
        name=f"Categoría Test {unique_id}",
        code=f"test_cat_{unique_id}",
        company_id=test_company.id,
        is_system=False,
        is_active=True
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)
    return category


@pytest_asyncio.fixture
async def test_permission(db_session: AsyncSession, test_company, test_permission_category):
    """Crear un permiso de prueba con identificadores únicos."""
    from app.models import Permission
    from uuid import uuid4

    unique_id = str(uuid4())[:8]
    permission = Permission(
        name=f"Permiso Test {unique_id}",
        code=f"test.perm.{unique_id}",
        resource="test",
        action="permission",
        company_id=test_company.id,
        category_id=test_permission_category.id,
        is_system=False,
        is_active=True
    )
    db_session.add(permission)
    await db_session.commit()
    await db_session.refresh(permission)
    return permission


@pytest_asyncio.fixture
async def test_role(db_session: AsyncSession, test_company):
    """Crear un rol de prueba con identificadores únicos."""
    from app.models import Role
    from uuid import uuid4

    unique_id = str(uuid4())[:8]
    role = Role(
        name=f"Rol Test {unique_id}",
        code=f"test_role_{unique_id}",
        company_id=test_company.id,
        hierarchy_level=50,
        is_system=False,
        is_active=True
    )
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)
    return role


@pytest_asyncio.fixture
async def test_role_permission(db_session: AsyncSession, test_role, test_permission):
    """Crear una asignación rol-permiso de prueba."""
    from app.models import RolePermission

    role_perm = RolePermission(
        role_id=test_role.id,
        permission_id=test_permission.id,
        granted_by=1  # Usuario admin por defecto
    )
    db_session.add(role_perm)
    await db_session.commit()
    await db_session.refresh(role_perm)
    return role_perm


# ==================== FIXTURES PARA PRODUCTOS ====================

# Fixtures síncronas para tests unitarios (mocks)
@pytest.fixture
def mock_category(test_company):
    """Mock de categoría para tests unitarios."""
    mock_cat = type('Category', (), {
        'id': 1,
        'name': "Categoría Mock",
        'company_id': test_company.id,
        'is_active': True
    })()
    return mock_cat

@pytest.fixture
def mock_product(test_company, mock_category):
    """Mock de producto para tests unitarios."""
    from decimal import Decimal
    mock_prod = type('Product', (), {
        'id': 1,
        'name': "Producto Mock",
        'price': Decimal('25.50'),
        'company_id': test_company.id,
        'category_id': mock_category.id,
        'is_active': True
    })()
    return mock_prod

# Fixtures async para tests de integración
@pytest_asyncio.fixture
async def test_category(db_session: AsyncSession, test_company):
    """Crear una categoría de prueba en BD."""
    from app.models import Category

    category = Category(
        name="Categoría de Prueba",
        description="Categoría para testing de productos",
        company_id=test_company.id,
        is_active=True
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)
    return category

@pytest_asyncio.fixture
async def test_product(db_session: AsyncSession, test_company, test_category):
    """Crear un producto de prueba en BD."""
    from app.models import Product
    from decimal import Decimal

    product = Product(
        name="Producto de Prueba",
        description="Descripción del producto de prueba",
        price=Decimal('25.50'),
        tax_rate=Decimal('0.10'),
        stock=Decimal('100.0'),
        image_url="https://example.com/image.jpg",
        company_id=test_company.id,
        category_id=test_category.id,
        is_active=True
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product

@pytest_asyncio.fixture
async def test_client():
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    # Usar ASGITransport para evitar warnings de Deprecation
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest.fixture
def user_token(test_user, test_company):
    """Generar token válido para el usuario de prueba."""
    from app.utils.security import create_access_token
    
    token_data = {
        "sub": test_user.username,
        "user_id": test_user.id,
        "company_id": test_company.id,
        "branch_id": 1, # Dummy branch ID if needed, or None
        "role": "admin",
        "plan": "premium",
        "username": test_user.username
    }
    return create_access_token(data=token_data)


@pytest_asyncio.fixture
async def test_branch(db_session: AsyncSession, test_company):
    """Crear una sucursal de prueba."""
    from app.models import Branch
    from uuid import uuid4
    
    unique_id = str(uuid4())[:8]
    branch = Branch(
        name=f"Sucursal Test {unique_id}",
        code=f"BR-{unique_id}",
        company_id=test_company.id,
        address="Dirección Sucursal Test",
        is_active=True
    )
    db_session.add(branch)
    await db_session.commit()
    await db_session.refresh(branch)
    return branch

@pytest_asyncio.fixture
async def test_products_batch(db_session: AsyncSession, test_company, test_category):
    """Crear un lote de productos de prueba en BD."""
    from app.models import Product
    from decimal import Decimal

    products = []
    for i in range(5):
        product = Product(
            name=f"Producto {i+1}",
            description=f"Descripción del producto {i+1}",
            price=Decimal(f'{(i+1) * 10}.00'),
            tax_rate=Decimal('0.10'),
            stock=Decimal(f'{i * 20}.0'),
            company_id=test_company.id,
            category_id=test_category.id,
            is_active=True
        )
        products.append(product)
        db_session.add(product)

    await db_session.commit()
    for product in products:
        await db_session.refresh(product)

    return products


@pytest_asyncio.fixture
async def test_company_2(db_session: AsyncSession):
    """Crear una segunda compañía con identificadores únicos para tests multi-tenant."""
    from app.models import Company
    from uuid import uuid4

    unique_id = str(uuid4())[:8]
    company = Company(
        name=f"Empresa Dos {unique_id}",
        slug=f"empresa-dos-{unique_id}",
        email=f"contacto-{unique_id}@empresa2.com",
        phone="+1234567890",
        address="Dirección Empresa 2",
        is_active=True
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)
    return company


@pytest_asyncio.fixture
async def test_user_company_2(db_session: AsyncSession, test_company_2):
    """Crear un usuario con identificadores únicos para la segunda compañía."""
    from app.models import User
    from app.utils.security import get_password_hash
    from uuid import uuid4

    unique_id = str(uuid4())[:8]
    user = User(
        username=f"user2-{unique_id}",
        email=f"user-{unique_id}@empresa2.com",
        full_name="Usuario Empresa 2",
        hashed_password=get_password_hash("testpass123"),
        company_id=test_company_2.id,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_category_company_2(db_session: AsyncSession, test_company_2):
    """Crear una categoría para la segunda compañía."""
    from app.models import Category

    category = Category(
        name="Categoría Empresa 2",
        description="Categoría de la empresa 2",
        company_id=test_company_2.id,
        is_active=True
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)
    return category


@pytest_asyncio.fixture
async def test_product_company_2(db_session: AsyncSession, test_company_2, test_category_company_2):
    """Crear un producto para la segunda compañía."""
    from app.models import Product
    from decimal import Decimal

    product = Product(
        name="Producto Empresa 2",
        description="Producto de la empresa 2",
        price=Decimal('15.00'),
        tax_rate=Decimal('0.05'),  # 5%
        stock=Decimal('50.0'),
        company_id=test_company_2.id,
        category_id=test_category_company_2.id,
        is_active=True
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product