# 🚀 Guía de Configuración Inicial del Sistema

Esta guía documenta el proceso necesario para preparar la base de datos antes de ejecutar tests o usar el sistema en desarrollo.

## 📋 Requisitos Previos

1. **Docker y Docker Compose** instalados
2. **Base de datos PostgreSQL** corriendo (via `docker-compose up -d`)
3. **Variables de entorno** configuradas en `.env`

## 🔧 Estado Requerido de la Base de Datos

Antes de ejecutar tests, la base de datos debe tener:

| Entidad | Mínimo Requerido | Detalles |
|---------|-----------------|----------|
| **Company** | 1 | Con slug `fastops` o similar |
| **Branch** | 1 | Al menos una sucursal por compañía |
| **Roles** | 4+ | `admin`, `cashier`, `kitchen`, `delivery` |
| **Permissions** | 12+ | Permisos CRUD básicos |
| **RolePermissions** | 10+ | Asignaciones de permisos a roles |
| **User Admin** | 1 | Usuario con rol `admin` y permisos |
| **Categories** | 1+ | Para tests de productos |

## 🌱 Proceso de Seeding

### Paso 1: Crear Tablas (Migraciones)
```bash
docker-compose exec backend alembic upgrade head
```

### Paso 2: Ejecutar Seed Master (Recomendado)
```bash
docker-compose exec backend python scripts/seed/master_seed.py --company fastops
```

Este script crea en orden:
1. ✅ Compañías
2. ✅ Categorías de permisos
3. ✅ Permisos
4. ✅ Roles
5. ✅ Usuarios
6. ✅ Asignaciones rol-permiso
7. ✅ Categorías de productos
8. ✅ Productos de ejemplo

### Paso 3: Seed de Permisos RBAC (Alternativo)
```bash
docker-compose exec backend python -m app.db.seed_permissions
```

## ⚠️ Problemas Comunes

### 1. No hay `RolePermissions` (0 registros)
**Síntoma**: Tests de permisos fallan con "Usuario sin permisos"
**Solución**: Ejecutar `master_seed.py` o `seed_permissions.py`

### 2. No hay Branch asociado
**Síntoma**: Tests que requieren `branch_id` fallan
**Solución**: El seed debe crear branches, o crear manualmente

### 3. Company "fastops" no existe
**Síntoma**: Seeds y tests no encuentran la compañía por defecto
**Solución**: Verificar que `data/seeds/companies.json` tiene la compañía correcta

## 🧪 Verificar Estado de la Base de Datos

```bash
docker-compose exec backend python -c "
import asyncio
from sqlalchemy import select
from app.database import get_session
from app.models import Company, User, Role, Permission, Branch, RolePermission

async def verify():
    async for session in get_session():
        companies = (await session.execute(select(Company))).scalars().all()
        roles = (await session.execute(select(Role))).scalars().all()
        users = (await session.execute(select(User))).scalars().all()
        perms = (await session.execute(select(Permission))).scalars().all()
        branches = (await session.execute(select(Branch))).scalars().all()
        rp = (await session.execute(select(RolePermission))).scalars().all()
        
        print('=== ESTADO DE LA BASE DE DATOS ===')
        print(f'Companies: {len(companies)}')
        print(f'Roles: {len(roles)}')
        print(f'Users: {len(users)}')
        print(f'Permissions: {len(perms)}')
        print(f'Branches: {len(branches)}')
        print(f'RolePermissions: {len(rp)}')
        
        if len(rp) == 0:
            print('\\n⚠️  ADVERTENCIA: No hay asignaciones de permisos a roles!')
        break

asyncio.run(verify())
"
```

## 📂 Archivos de Seed

Los datos de seed están en `data/seeds/`:

- `companies.json` - Compañías del sistema
- `roles.json` - Roles predefinidos
- `permissions.json` - Permisos del sistema
- `permission_categories.json` - Categorías de permisos
- `role_permissions.json` - Asignaciones rol-permiso
- `users.json` - Usuarios de prueba
- `categories.json` - Categorías de productos
- `products.json` - Productos de ejemplo

## 🔄 Reset Completo

Para reiniciar la base de datos completamente:

```bash
# Opción 1: Reset via Alembic
docker-compose exec backend alembic downgrade base
docker-compose exec backend alembic upgrade head
docker-compose exec backend python scripts/seed/master_seed.py --reset

# Opción 2: Recrear contenedor de DB
docker-compose down -v
docker-compose up -d
docker-compose exec backend alembic upgrade head
docker-compose exec backend python scripts/seed/master_seed.py
```
