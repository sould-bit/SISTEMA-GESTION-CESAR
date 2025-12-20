# 🧪 TESTS AUTOMATIZADOS - FastOps SaaS

Este directorio contiene todos los tests automatizados del sistema backend, organizados por tipo y funcionalidad.

## 📁 Estructura de Tests

```
backend/tests/
├── __init__.py              # Configuración del paquete de tests
├── conftest.py              # Fixtures globales y configuración
├── services/                # Tests unitarios de servicios
│   ├── test_auth_service.py     # 🔐 AuthService
│   └── test_category_service.py # 🗂️ CategoryService
├── repositories/            # Tests unitarios de repositorios
│   └── test_base_repository.py  # 🏗️ BaseRepository
├── routers/                 # Tests de integración de routers
│   ├── test_auth_router.py      # 🌐 Auth Router
│   └── test_category_router.py  # 🌐 Category Router
└── README.md                # Este archivo
```

## 🚀 Ejecutar Tests

### Todos los tests
```bash
cd backend
pytest
```

### Tests específicos
```bash
# Solo tests de servicios
pytest tests/services/

# Solo tests de integración
pytest tests/routers/

# Test específico
pytest tests/services/test_auth_service.py::TestAuthService::test_authenticate_user_success -v

# Con coverage
pytest --cov=app --cov-report=html
```

### Tests por tipo
```bash
# Unit tests
pytest -m unit

# Integration tests
pytest -m integration

# Tests con base de datos
pytest -m database
```

## 🛠️ Configuración de Testing

### Base de Datos de Testing
- **Motor**: SQLite en memoria (`:memory:`)
- **Ventajas**: Rápido, independiente, sin estado persistente
- **Fixtures**: Automática creación/limpieza por test

### Fixtures Disponibles

#### Globales (`conftest.py`)
- `db_session`: Sesión de BD limpia por test
- `test_client`: Cliente FastAPI para integration tests
- `auth_service`: Instancia de AuthService
- `category_service`: Instancia de CategoryService
- `test_company`: Empresa de prueba
- `test_user`: Usuario de prueba
- `test_category`: Categoría de prueba
- `auth_token`: Token JWT válido
- `auth_headers`: Headers con Authorization

### Datos de Prueba
Los fixtures crean automáticamente:
- ✅ Empresa: `test-company` con slug `test-company`
- ✅ Usuario: `testuser` / `testpass123` (admin)
- ✅ Categoría: `Test Category`

## 📋 Cobertura de Tests

### 🔐 AuthService (Unit Tests)
- ✅ Login exitoso con credenciales válidas
- ✅ Login fallido (contraseña incorrecta, usuario inexistente)
- ✅ Usuario inactivo rechazado
- ✅ Empresa inexistente
- ✅ Generación de tokens JWT
- ✅ Validación de usuarios
- ✅ Refresh tokens
- ✅ Logout

### 🗂️ CategoryService (Unit Tests)
- ✅ Listar categorías por empresa
- ✅ Crear categoría con validación de unicidad
- ✅ Crear categoría duplicada (falla correctamente)
- ✅ Obtener categoría por ID
- ✅ Actualizar categoría
- ✅ Eliminar categoría (soft delete)
- ✅ Validaciones multi-tenant

### 🏗️ BaseRepository (Unit Tests)
- ✅ Operaciones CRUD básicas
- ✅ Filtros multi-tenant automáticos
- ✅ Manejo de transacciones
- ✅ Validaciones de existencia
- ✅ Conteo de registros
- ✅ Paginación

### 🌐 Auth Router (Integration Tests)
- ✅ POST /auth/login - Login exitoso y fallido
- ✅ GET /auth/me - Usuario actual autenticado
- ✅ GET /auth/verify - Verificación de token
- ✅ POST /auth/refresh - Refresh token
- ✅ POST /auth/logout - Logout
- ✅ Validaciones de autenticación
- ✅ Manejo de errores HTTP

### 🌐 Category Router (Integration Tests)
- ✅ GET /categories/ - Listar categorías
- ✅ POST /categories/ - Crear categoría
- ✅ GET /categories/{id} - Obtener específica
- ✅ PUT /categories/{id} - Actualizar
- ✅ DELETE /categories/{id} - Eliminar
- ✅ Validaciones multi-tenant
- ✅ Manejo de errores HTTP

## 🔒 Seguridad Multi-Tenant

Todos los tests verifican el **aislamiento completo** entre empresas:

```python
# ✅ AISLAMIENTO VERIFICADO
# Categorías con mismo nombre en empresas diferentes
company1_data = {"name": "Shared Name", "company_id": 1}
company2_data = {"name": "Shared Name", "company_id": 2}

# Ambas creaciones funcionan correctamente
# Listados separados no muestran datos de otras empresas
```

## 📊 Métricas de Calidad

### Cobertura Objetivo
- **Líneas**: > 80%
- **Ramas**: > 75%
- **Funciones**: > 90%

### Rendimiento
- **Tests unitarios**: < 100ms cada uno
- **Tests de integración**: < 500ms cada uno
- **Suite completa**: < 30 segundos

## 🐛 Debugging

### Ver logs detallados
```bash
pytest -v -s --log-cli-level=DEBUG
```

### Debug específico
```bash
pytest --pdb tests/services/test_auth_service.py::TestAuthService::test_authenticate_user_success
```

### Ver fixtures disponibles
```bash
pytest --fixtures
```

## 📝 Agregar Nuevos Tests

### 1. Para nuevos servicios
```python
# backend/tests/services/test_new_service.py
class TestNewService:
    @pytest.mark.asyncio
    async def test_method_success(self, new_service: NewService):
        # Arrange
        # Act
        # Assert
```

### 2. Para nuevos routers
```python
# backend/tests/routers/test_new_router.py
class TestNewRouter:
    @pytest.mark.asyncio
    async def test_endpoint_success(self, test_client: AsyncClient, auth_headers: dict):
        # Arrange
        # Act
        response = await test_client.get("/new-endpoint", headers=auth_headers)
        # Assert
        assert response.status_code == 200
```

## 🔧 Comandos Útiles

```bash
# Instalar dependencias de testing
pip install -r requirements-test.txt

# Ejecutar con diferentes reporters
pytest --html=report.html --self-contained-html
pytest --cov=app --cov-report=xml

# Ejecutar tests modificados recientemente
pytest --last-failed
pytest --failed-first

# Paralelizar tests
pytest -n auto
```

## 📈 Mejores Prácticas

### ✅ HACER
- Usar fixtures para setup/teardown
- Tests independientes (no dependen de orden)
- Nombres descriptivos: `test_login_success`
- Un solo assert por test cuando sea posible
- Mockear dependencias externas

### ❌ NO HACER
- Tests que dependan del estado global
- Tests que modifiquen datos compartidos
- Nombres vagos: `test_function`
- Tests que fallen intermitentemente
- Tests que requieran configuración manual

## 🎯 Próximos Pasos

1. **Agregar más servicios**: UserService, CompanyService, etc.
2. **Tests de carga**: Verificar rendimiento
3. **Tests de seguridad**: SQL injection, XSS, etc.
4. **CI/CD**: Integración con GitHub Actions
5. **Reportes**: Dashboards de calidad de código

---

**Mantén los tests actualizados** con cada cambio en el código. Los tests son la red de seguridad del proyecto. 🛡️
