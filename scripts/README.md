# 🔧 Scripts Utilitarios

Scripts para desarrollo, deployment y mantenimiento del sistema FastAPI RBAC.

## 📁 Estructura

```
scripts/
├── admin/          # Scripts de administración del sistema
├── seed/           # Scripts para poblar datos iniciales
├── run_tests.py    # Ejecutor de tests personalizado
├── debug_config.py # Utilidades de debugging
└── factories.py    # Factories para desarrollo/testing
```

## 🚀 Scripts Disponibles

### Administración (`admin/`)

#### `create_admin.py`
Crea usuario administrador inicial.
```bash
python scripts/admin/create_admin.py
```

#### `create_tables.py`
Crea tablas de base de datos manualmente (alternativo a Alembic).
```bash
python scripts/admin/create_tables.py
```

### Seeds (`seed/`)

#### `seed_simple.py`
Inserta datos básicos para desarrollo.
```bash
python scripts/seed/seed_simple.py
```

#### `seed_data_script.py`
Script avanzado de seeding con validaciones.
```bash
python scripts/seed/seed_data_script.py
```

### Utilidades

#### `run_tests.py`
Ejecutor personalizado de tests con opciones avanzadas.
```bash
python scripts/run_tests.py
```

#### `debug_config.py`
Herramientas de debugging para configuración.
```bash
python scripts/debug_config.py
```

#### `factories.py`
Factories para generar datos de prueba.
```python
from scripts.factories import UserFactory, RoleFactory
```

## 🔄 Flujo de Desarrollo

1. **Setup inicial:**
   ```bash
   python scripts/admin/create_tables.py
   python scripts/admin/create_admin.py
   ```

2. **Poblar datos:**
   ```bash
   python scripts/seed/seed_simple.py
   ```

3. **Testing:**
   ```bash
   python scripts/run_tests.py
   ```

## ⚠️ Notas Importantes

- Los scripts están diseñados para desarrollo, no usar en producción
- Verificar configuración de base de datos antes de ejecutar
- Algunos scripts requieren variables de entorno específicas
