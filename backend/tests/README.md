# 🧪 Sistema de Pruebas - RBAC

Este directorio contiene todas las pruebas del sistema RBAC (Role-Based Access Control).

## 📁 Estructura

```
tests/
├── conftest.py              # Configuración global y fixtures
├── services/               # Pruebas de servicios
│   ├── test_permission_service.py
│   └── test_role_service.py
├── routers/                # Pruebas de endpoints (futuro)
├── repositories/           # Pruebas de repositorios (futuro)
├── test_permissions_decorators.py  # Pruebas de decoradores
└── README.md              # Esta documentación
```

## 🚀 Ejecutar Pruebas

### Opción 1: Script Principal (Recomendado)
```bash
# Pruebas completas con integración
python test_rbac_integration.py

# Validación rápida (solo sistema básico)
python test_rbac_integration.py --quick
```

### Opción 2: Script de Pruebas General
```bash
# Todas las pruebas
python run_tests.py

# Solo pruebas RBAC
python run_tests.py --rbac

# Con reporte de cobertura
python run_tests.py --coverage

# Prueba específica
python run_tests.py --file tests/services/test_role_service.py
```

### Opción 3: Pytest Directo
```bash
# Todas las pruebas
pytest

# Pruebas unitarias
pytest -m unit

# Pruebas RBAC
pytest -m rbac

# Con cobertura
pytest --cov=app --cov-report=html

# Prueba específica
pytest tests/services/test_role_service.py -v
```

## 📋 Tipos de Pruebas

### 🧩 Unitarias (`@pytest.mark.unit`)
Pruebas que validan componentes individuales:
- Servicios (RoleService, PermissionService)
- Funciones utilitarias
- Validaciones de modelos

### 🔗 Integración (`@pytest.mark.integration`)
Pruebas que validan la interacción entre componentes:
- Endpoints completos
- Flujos de autenticación/autorización
- Integración con base de datos

### 🔐 RBAC (`@pytest.mark.rbac`)
Pruebas específicas del sistema de roles y permisos:
- Verificación de permisos
- Asignación de roles
- Decoradores de autorización

## 🛠️ Fixtures Disponibles

### Datos de Prueba
- `test_company`: Empresa de prueba
- `test_user`: Usuario de prueba
- `test_role`: Rol de prueba
- `test_permission`: Permiso de prueba
- `test_permission_category`: Categoría de permisos

### Utilidades
- `db_session`: Sesión de base de datos limpia
- `mock_redis`: Mock de Redis para pruebas

## 📊 Reportes

### Cobertura
```bash
pytest --cov=app --cov-report=html
# Abre htmlcov/index.html en el navegador
```

### Resultados Detallados
```bash
pytest -v --tb=long
```

## 🔧 Debugging

### Ejecutar Prueba Específica
```bash
pytest tests/services/test_role_service.py::TestRoleService::test_create_role -v -s
```

### Ver Todas las Pruebas
```bash
pytest --collect-only
```

### Ejecutar con PDB
```bash
pytest --pdb
```

## 📝 Agregar Nuevas Pruebas

### 1. Estructura de Clase
```python
import pytest

class TestMiServicio:
    """Pruebas para MiServicio."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_mi_funcion(self, db_session, test_user):
        """Test que valida mi función."""
        # Arrange
        # Act
        # Assert
```

### 2. Marcadores
```python
@pytest.mark.unit      # Prueba unitaria
@pytest.mark.rbac      # Específica de RBAC
@pytest.mark.slow      # Prueba lenta
```

### 3. Fixtures Personalizadas
Agregar en `conftest.py` para compartir entre pruebas.

## 🚨 Casos Especiales

### Pruebas que Requieren Redis
```python
@pytest.mark.redis
async def test_con_cache(mock_redis):
    """Esta prueba necesita Redis."""
```

### Pruebas de Seguridad
```python
async def test_acceso_denegado(self, db_session, test_user):
    """Verificar que se bloquee acceso sin permisos."""
    with pytest.raises(HTTPException) as exc:
        # Código que debe fallar
        assert exc.value.status_code == 403
```

## 📈 Métricas de Calidad

- **Cobertura Objetivo**: >85%
- **Tiempo de Ejecución**: <30 segundos
- **Pruebas por Servicio**: Mínimo 10 pruebas

## 🔄 CI/CD

Las pruebas se ejecutan automáticamente en:
- Push a rama main
- Pull requests
- Deploy a producción

```yaml
# En GitHub Actions
- name: Run Tests
  run: |
    cd backend
    python test_rbac_integration.py
```

## 🐛 Reportar Issues

Si encuentras un bug en las pruebas:
1. Reproducir el error
2. Ejecutar con `--tb=long` para detalles
3. Crear issue con logs completos
