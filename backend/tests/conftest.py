"""
🛠️ CONFIGURACIÓN GLOBAL DE TESTS - Fixtures y Setup

Este archivo contiene todas las fixtures necesarias para ejecutar los tests:
- Base de datos de testing (SQLite en memoria)
- Clientes FastAPI de testing
- Servicios mockeados
- Datos de prueba (usuarios, compañías)

Fixtures disponibles:
- db_session: Sesión de BD para tests
- test_client: Cliente FastAPI para integration tests
- auth_service: Instancia de AuthService
- category_service: Instancia de CategoryService
- test_user: Usuario de prueba
- test_company: Compañía de prueba
"""

import asyncio
from typing import Generator, AsyncGenerator
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# Importamos solo lo necesario para evitar configuración de BD de producción
# from app.main import app  # No importamos aquí para evitar configuración de BD
# from app.database import get_session  # No importamos aquí
from app.services import AuthService, CategoryService
from app.models.user import User
from app.models.company import Company
from app.models.category import Category
from app.utils.security import get_password_hash
from app.utils.security import get_password_hash


# ============================================
# CONFIGURACIÓN DE BASE DE DATOS DE TESTING
# ============================================

# Usar SQLite en memoria para tests (más rápido que PostgreSQL)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Engine de testing
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,  # Cambiar a True para debug
    future=True,
)

# Session maker para tests
TestSessionLocal = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Crear event loop para tests async"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


import pytest_asyncio

@pytest_asyncio.fixture(scope="session")
async def setup_database() -> None:
    """
    🗄️ SETUP DE BASE DE DATOS PARA TESTS

    Crea todas las tablas antes de ejecutar los tests.
    Se ejecuta una sola vez por sesión de testing.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield

    # Cleanup después de todos los tests
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(setup_database: None) -> AsyncGenerator[AsyncSession, None]:
    """
    🗃️ SESIÓN DE BASE DE DATOS PARA TESTS

    Proporciona una sesión limpia de BD para cada test.
    Se hace rollback automático después de cada test.
    """
    async with TestSessionLocal() as session:
        # Crear datos de prueba para cada test
        await create_test_data(session)

        yield session

        # Rollback para limpiar cambios
        await session.rollback()


async def create_test_data(session: AsyncSession):
    """
    📝 CREAR DATOS DE PRUEBA

    Inserta datos básicos necesarios para los tests.
    """
    # Crear compañía de prueba
    test_company = Company(
        name="Test Company",
        slug="test-company",
        legal_name="Test Company S.A.S.",
        tax_id="123456789",
        owner_name="Test Owner",
        owner_email="owner@test.com",
        owner_phone="3001234567",
        plan="trial",
        is_active=True,
        timezone="America/Bogota",
        currency="COP"
    )
    session.add(test_company)
    await session.flush()  # Para obtener el ID

    # Crear usuario de prueba
    test_user = User(
        company_id=test_company.id,
        branch_id=None,  # Usuario sin sucursal asignada
        username="testuser",
        email="test@test.com",
        full_name="Test User",
        hashed_password=get_password_hash("testpass123"),
        role="admin",
        is_active=True
    )
    session.add(test_user)

    # Crear categoría de prueba
    test_category = Category(
        company_id=test_company.id,
        name="Test Category",
        description="Categoría para tests",
        is_active=True
    )
    session.add(test_category)

    await session.commit()


# ============================================
# FIXTURES DE SERVICIOS
# ============================================

@pytest.fixture
def auth_service(db_session: AsyncSession) -> AuthService:
    """
    🔐 SERVICIO DE AUTENTICACIÓN PARA TESTS

    Proporciona instancia de AuthService con BD de testing.
    """
    return AuthService(db_session)


@pytest.fixture
async def category_service(db_session: AsyncSession) -> CategoryService:
    """
    🗂️ SERVICIO DE CATEGORÍAS PARA TESTS

    Proporciona instancia de CategoryService con BD de testing.
    """
    return CategoryService(db_session)


# ============================================
# FIXTURES DE DATOS DE PRUEBA
# ============================================

@pytest.fixture
async def test_company(db_session: AsyncSession) -> Company:
    """
    🏢 COMPAÑÍA DE PRUEBA

    Retorna la compañía creada en create_test_data.
    """
    result = await db_session.execute(
        SQLModel.select(Company).where(Company.slug == "test-company")
    )
    return result.scalar_one()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """
    👤 USUARIO DE PRUEBA

    Retorna el usuario creado en create_test_data.
    """
    result = await db_session.execute(
        SQLModel.select(User).where(User.username == "testuser")
    )
    return result.scalar_one()


@pytest.fixture
async def test_category(db_session: AsyncSession) -> Category:
    """
    🗂️ CATEGORÍA DE PRUEBA

    Retorna la categoría creada en create_test_data.
    """
    result = await db_session.execute(
        SQLModel.select(Category).where(Category.name == "Test Category")
    )
    return result.scalar_one()


# ============================================
# FIXTURE PARA CLIENTE FASTAPI (INTEGRATION TESTS)
# ============================================

@pytest_asyncio.fixture
async def test_client(setup_database: None) -> AsyncGenerator[AsyncClient, None]:
    """
    🌐 CLIENTE FASTAPI PARA TESTS DE INTEGRACIÓN

    Proporciona cliente HTTP para probar endpoints completos.
    Override la dependencia de BD para usar BD de testing.
    """
    # Importar aquí para evitar configuración de BD de producción
    from app.main import app
    from app.database import get_session

    async def override_get_session():
        """Override para usar BD de testing en lugar de producción"""
        async with TestSessionLocal() as session:
            await create_test_data(session)
            yield session

    # Override la dependencia
    app.dependency_overrides[get_session] = override_get_session

    # Crear cliente
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client

    # Limpiar overrides
    app.dependency_overrides.clear()


# ============================================
# FIXTURES PARA AUTENTICACIÓN EN TESTS
# ============================================

@pytest.fixture
async def auth_token(test_client: AsyncClient) -> str:
    """
    🎫 TOKEN JWT PARA TESTS AUTENTICADOS

    Realiza login y retorna token JWT válido para usar en tests.
    """
    login_data = {
        "company_slug": "test-company",
        "username": "testuser",
        "password": "testpass123"
    }

    response = await test_client.post("/auth/login", json=login_data)
    assert response.status_code == 200

    data = response.json()
    return data["access_token"]


@pytest.fixture
async def auth_headers(auth_token: str) -> dict:
    """
    📋 HEADERS DE AUTENTICACIÓN

    Retorna headers con Authorization Bearer para requests autenticados.
    """
    return {"Authorization": f"Bearer {auth_token}"}
