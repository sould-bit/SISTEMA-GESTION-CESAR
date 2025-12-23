# 📊 Datos del Sistema

Datos estáticos y de configuración para FastAPI RBAC System.

## 📁 Estructura

```
data/
└── seeds/          # Datos iniciales para seeding
```

## 🌱 Seeds (`seeds/`)

Archivos con datos predefinidos para poblar la base de datos en desarrollo y testing.

### Archivos incluidos:
- `roles.json` - Roles del sistema
- `permissions.json` - Permisos base
- `categories.json` - Categorías de permisos
- `companies.json` - Empresas de ejemplo
- `users.json` - Usuarios de prueba

### Formato:
Los archivos están en formato JSON para facilitar la edición y mantenimiento.

```json
{
  "roles": [
    {
      "name": "Administrador",
      "code": "admin",
      "hierarchy_level": 100,
      "is_system": true
    }
  ]
}
```

## 🚀 Uso

Los datos de seed son utilizados por los scripts en `scripts/seed/` para poblar la base de datos inicial.

### Cargar seeds automáticamente:
```bash
python scripts/seed/seed_simple.py
```

### Cargar seeds específicos:
```bash
python scripts/seed/seed_data_script.py --file roles
```

## 🔧 Mantenimiento

### Agregar nuevos seeds:
1. Crear archivo JSON en `data/seeds/`
2. Actualizar scripts de seed para incluir el nuevo archivo
3. Probar con datos de desarrollo

### Modificar seeds existentes:
1. Editar archivo JSON correspondiente
2. Ejecutar tests para validar cambios
3. Actualizar documentación si es necesario

## ⚠️ Consideraciones

- Los seeds son solo para desarrollo/testing
- No modificar seeds en producción
- Mantener consistencia entre archivos relacionados
- Documentar cualquier cambio en este README
