# 🧪 Tests Suite

Suite completa de pruebas para FastAPI RBAC System.

## 📁 Estructura

```
tests/
├── unit/           # Pruebas unitarias de componentes individuales
├── integration/    # Pruebas de integración entre componentes
└── e2e/           # Pruebas end-to-end completas
```

## 🚀 Ejecución

### Todos los tests:
```bash
pytest
```

### Tests específicos:
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# E2E tests
pytest tests/e2e/
```

### Con coverage:
```bash
pytest --cov=app --cov-report=html
```

## 📋 Tipos de Tests

### Unit Tests (`unit/`)
- Pruebas de funciones individuales
- Mocks para dependencias externas
- Cobertura de casos edge

### Integration Tests (`integration/`)
- Pruebas de interacción entre servicios
- Base de datos en memoria (SQLite)
- Validación de flujos completos

### E2E Tests (`e2e/`)
- Pruebas contra aplicación completa
- Base de datos real
- Validación de APIs RESTful

## 🛠️ Configuración

Los tests usan `pytest.ini` para configuración global y `conftest.py` para fixtures compartidas.
