"""
Configuración global de pruebas para el sistema RBAC.

Este archivo contiene fixtures y configuraciones compartidas
para todas las pruebas del sistema.
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

# from app.database import get_session
# from app.config import settings


# Configuración de base de datos en memoria para pruebas
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Engine de pruebas (lazy initialization)
test_engine = None
TestSessionLocal = None

def get_test_engine():
    """Obtener engine de pruebas (lazy loading)."""
    global test_engine, TestSessionLocal
    if test_engine is None:
        test_engine = create_async_engine(
            TEST_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
        TestSessionLocal = async_sessionmaker(
            bind=test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return test_engine, TestSessionLocal


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Crear event loop para pruebas asíncronas."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    """Configurar base de datos para pruebas."""
    engine, _ = get_test_engine()
    # Crear todas las tablas
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield

    # Limpiar después de las pruebas
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture
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


# Fixture para crear datos de prueba comunes (simplificados)
@pytest.fixture
async def test_company(db_session: AsyncSession):
    """Crear una compañía de prueba."""
    # Crear objeto Company simplificado sin importar el modelo completo
    company = type('Company', (), {
        'id': 1,
        'name': "Empresa de Prueba",
        'slug': "empresa-prueba",
        'is_active': True
    })()
    # En una implementación real, aquí crearías el registro en BD
    return company


@pytest.fixture
async def test_user(db_session: AsyncSession, test_company):
    """Crear un usuario de prueba."""
    from app.models import User
    from app.utils.security import get_password_hash

    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Usuario de Prueba",
        hashed_password=get_password_hash("testpass123"),
        company_id=test_company.id,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_permission_category(db_session: AsyncSession, test_company):
    """Crear una categoría de permisos de prueba."""
    from app.models import PermissionCategory

    category = PermissionCategory(
        name="Categoría de Prueba",
        code="test_category",
        company_id=test_company.id,
        is_system=False,
        is_active=True
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)
    return category


@pytest.fixture
async def test_permission(db_session: AsyncSession, test_company, test_permission_category):
    """Crear un permiso de prueba."""
    from app.models import Permission

    permission = Permission(
        name="Permiso de Prueba",
        code="test.permission",
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


@pytest.fixture
async def test_role(db_session: AsyncSession, test_company):
    """Crear un rol de prueba."""
    from app.models import Role

    role = Role(
        name="Rol de Prueba",
        code="test_role",
        company_id=test_company.id,
        hierarchy_level=50,
        is_system=False,
        is_active=True
    )
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)
    return role


@pytest.fixture
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