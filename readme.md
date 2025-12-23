# 🚀 FastAPI RBAC System

Sistema completo de control de acceso basado en roles (RBAC) construido con FastAPI, SQLModel y PostgreSQL.

## 📁 Estructura del Proyecto

```
backend/
├── app/                    # Código principal de la aplicación
│   ├── core/              # Componentes core (auth, cache, logging)
│   ├── models/            # Modelos SQLModel
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Lógica de negocio
│   ├── routers/           # Endpoints FastAPI
│   └── db/                # Configuración de BD
├── tests/                 # Suite completa de tests
│   ├── unit/             # Tests unitarios
│   ├── integration/      # Tests de integración
│   └── e2e/              # Tests end-to-end
├── scripts/               # Scripts utilitarios
│   ├── admin/            # Scripts de administración
│   ├── seed/             # Scripts de seeding
│   └── dev_utils.py      # Utilidades de desarrollo
├── data/                  # Datos estáticos
│   └── seeds/            # Archivos JSON de seed
├── migrations/            # Migraciones Alembic
├── logs/                  # Logs de aplicación
└── Dockerfile             # Configuración Docker
```

## 🚀 Inicio Rápido

### Prerrequisitos
- Docker y Docker Compose
- Python 3.12+
- PostgreSQL (incluido en Docker)

### Setup Completo
```bash
# Clonar repositorio
git clone <repository-url>
cd SISTEMA-GESTION-CESAR/backend

# Setup automático (construye, inicia servicios, migra y seed)
python scripts/dev_utils.py setup
```

### Verificación
- **API Docs**: http://localhost:8000/docs
- **Login**: `admin` / `admin123`
- **PgAdmin**: http://localhost:5050

## 🔧 Comandos Útiles

```bash
# Desarrollo
python scripts/dev_utils.py setup      # Setup completo
python scripts/dev_utils.py seed       # Poblar datos
python scripts/dev_utils.py test       # Ejecutar tests
python scripts/dev_utils.py logs       # Ver logs

# Base de datos
python scripts/dev_utils.py reset-db   # Reset completo de BD

# Limpieza
python scripts/dev_utils.py clean      # Limpiar temporales
```

## 📚 API Endpoints

### Autenticación
- `POST /auth/login` - Login de usuario
- `POST /auth/refresh` - Refresh token

### Roles y Permisos
- `GET /rbac/roles` - Listar roles
- `GET /rbac/roles/{id}` - Detalle de rol con permisos
- `POST /rbac/roles` - Crear rol
- `PUT /rbac/roles/{id}` - Actualizar rol
- `DELETE /rbac/roles/{id}` - Eliminar rol

- `GET /rbac/permissions` - Listar permisos
- `POST /rbac/permissions` - Crear permiso
- `POST /rbac/roles/{role_id}/permissions/{perm_id}` - Asignar permiso

### Sistema
- `GET /health` - Health check
- `GET /bd-test` - Test de conexión BD

## 🧪 Testing

### Ejecutar Tests
```bash
# Todos los tests
python scripts/dev_utils.py test

# Tests específicos
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/e2e/          # End-to-end tests

# Con coverage
pytest --cov=app --cov-report=html
```

### Estructura de Tests
- **Unit**: Componentes individuales (funciones, clases)
- **Integration**: Interacción entre servicios
- **E2E**: Flujos completos contra API real

## 🌱 Seeding de Datos

Los datos iniciales están organizados en archivos JSON:

```bash
data/seeds/
├── companies.json      # Empresas
├── roles.json          # Roles del sistema
├── permissions.json    # Permisos disponibles
├── permission_categories.json  # Categorías
├── users.json          # Usuarios de prueba
└── role_permissions.json       # Asignaciones
```

### Ejecutar Seed
```bash
python scripts/seed/master_seed.py
```

## 🏗️ Arquitectura

### Características Principales
- ✅ **Multi-tenancy** completo
- ✅ **RBAC avanzado** con jerarquía
- ✅ **Caché Redis** para performance
- ✅ **Logging JSON** estructurado
- ✅ **Excepciones personalizadas**
- ✅ **Testing completo**
- ✅ **Docker containerizado**

### Tecnologías
- **FastAPI** - Framework web moderno
- **SQLModel** - ORM con Pydantic
- **PostgreSQL** - Base de datos
- **Redis** - Caché y sesiones
- **Docker** - Containerización
- **Pytest** - Testing framework

## 🔒 Seguridad

- JWT tokens con refresh
- Hashing bcrypt para passwords
- Validación automática de permisos
- Rate limiting
- CORS configurado
- Logs de seguridad

## 📊 Monitoreo

- Health checks automáticos
- Logs JSON estructurados
- Métricas de performance
- Alertas de errores

## 🚀 Deployment

### Producción
```bash
# Usar docker-compose.prod.yml
docker-compose -f docker-compose.prod.yml up -d

# Variables de entorno requeridas
cp .env.example .env.prod
# Configurar variables de prod
```

### Desarrollo
```bash
# Ambiente de desarrollo
docker-compose up -d

# Hot reload activado
# Logs en tiempo real
```

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 📞 Soporte

Para soporte técnico o preguntas:
- 📧 Email: support@fastops.com
- 📖 Docs: [Documentación completa](docs/)
- 🐛 Issues: [GitHub Issues](issues/)

---

**Desarrollado con ❤️ para sistemas de gestión empresarial**