# 🚀 FastOps - Sistema de Gestión para Comida Rápida

**Plataforma SaaS multi-tenant** para gestión integral de salchipapererías y negocios de comida rápida. Construido con FastAPI, SQLModel y PostgreSQL.

## 📁 Estructura del Proyecto

```
backend/
├── app/                    # Código principal de la aplicación
│   ├── core/              # Componentes core (auth, cache, logging)
│   ├── models/            # 22 Modelos SQLModel
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # 22 Servicios de lógica de negocio
│   ├── routers/           # 13 Endpoints FastAPI
│   ├── repositories/      # Capa de acceso a datos
│   ├── db/                # Configuración de BD
│   ├── utils/             # Utilidades
│   └── tasks/             # Tareas asíncronas
├── tests/                 # Suite completa de tests
│   ├── unit/             # Tests unitarios
│   ├── integration/      # Tests de integración
│   ├── e2e/              # Tests end-to-end
│   └── load/             # Tests de carga
├── scripts/               # Scripts utilitarios
│   ├── admin/            # Scripts de administración
│   ├── seed/             # Scripts de seeding
│   └── dev_utils.py      # Utilidades de desarrollo
├── data/                  # Datos estáticos
│   └── seeds/            # Archivos JSON de seed
├── migrations/            # Migraciones Alembic
├── logs/                  # Logs de aplicación
└── Dockerfile             # Configuración Docker

pwa customers/             # PWA para clientes finales
docuemntos_de_desarrollo/  # Documentación técnica del proyecto
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
- **Login Admin**: `admin` / `admin123`
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

## 📚 Módulos del Sistema

### 🔐 Autenticación y RBAC
- `POST /auth/login` - Login de usuario
- `POST /auth/refresh` - Refresh token
- `GET /rbac/roles` - Listar roles
- `POST /rbac/roles` - Crear rol
- `GET /rbac/permissions` - Listar permisos
- `POST /rbac/roles/{role_id}/permissions/{perm_id}` - Asignar permiso

### 🏢 Multi-tenant
- Aislamiento completo por `company_id` y `branch_id`
- Gestión de empresas y sucursales
- Suscripciones por tenant

### 📦 Productos y Categorías
- `GET/POST/PUT/DELETE /products/*` - CRUD completo de productos
- `GET/POST/PUT/DELETE /categories/*` - Gestión de categorías multi-tenant
- Validaciones de negocio (precio > 0, nombre único por empresa)
- Soft deletes

### 🍳 Sistema de Recetas
- `GET/POST/PUT/DELETE /recipes/*` - CRUD de recetas
- Cálculo automático de costos por ingredientes
- Integración con inventario

### 📋 Sistema de Pedidos
- `GET/POST/PUT /orders/*` - Gestión de pedidos
- Máquina de estados para flujo de pedidos
- Contador de órdenes diarias
- Integración con inventario y recetas
- Deducción automática de stock

### 📦 Inventario
- `GET/POST/PUT /inventory/*` - Gestión de inventario
- Control de stock por sucursal
- Movimientos y ajustes
- Alertas de stock bajo

### 🛵 Módulo de Delivery
- `GET/POST/PUT /delivery/*` - Control de entregas
- Gestión de turnos de domiciliarios (`DeliveryShift`)
- Asignación de pedidos a repartidores
- Tracking de entregas en tiempo real

### 👥 CRM y Clientes
- `GET/POST/PUT /customers/*` - Gestión de clientes
- Direcciones de entrega múltiples
- Historial de pedidos
- Registro de clientes

### 🛒 Storefront (PWA)
- `GET/POST /storefront/*` - API dedicada para PWA de clientes
- Registro y login de clientes
- Browse de sucursales
- Visualización de menú
- Creación de pedidos desde PWA

### 💰 Caja y Pagos
- `GET/POST /cash/*` - Sistema de caja
- `GET/POST /payments/*` - Procesamiento de pagos
- Cierre de caja diario
- Múltiples métodos de pago

### 📊 Reportes
- `GET /reports/*` - Dashboard y analytics
- Reportes de ventas
- Métricas de rendimiento

## 🧪 Testing

### Ejecutar Tests
```bash
# Todos los tests
python scripts/dev_utils.py test

# Tests específicos
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/e2e/          # End-to-end tests
pytest tests/load/         # Load tests

# Con coverage
pytest --cov=app --cov-report=html
```

### Flujos de Test E2E
- `test_admin_flow.py` - Flujo completo de administración
- `test_customer_flow.py` - Flujo de cliente en PWA

## 🌱 Seeding de Datos

Los datos iniciales están organizados en archivos JSON:

```bash
data/seeds/
├── companies.json         # Empresas
├── branches.json          # Sucursales
├── roles.json             # Roles del sistema
├── permissions.json       # Permisos disponibles
├── permission_categories.json  # Categorías de permisos
├── users.json             # Usuarios de prueba
├── products.json          # Productos de ejemplo
├── categories.json        # Categorías de productos
├── inventory.json         # Stock inicial
└── role_permissions.json  # Asignaciones rol-permiso
```

### Ejecutar Seed
```bash
python scripts/seed/master_seed.py
```

## 🏗️ Arquitectura

### Características Principales
- ✅ **Multi-tenancy** completo por company/branch
- ✅ **RBAC avanzado** con jerarquía y caché
- ✅ **Caché Redis** para performance
- ✅ **Logging JSON** estructurado
- ✅ **Excepciones personalizadas**
- ✅ **Máquina de estados** para pedidos
- ✅ **Testing completo** (unit, integration, e2e, load)
- ✅ **Docker containerizado**
- ✅ **PWA para clientes** (Storefront)
- ✅ **Sistema de delivery** con turnos

### Modelos de Datos (22 modelos)
- **Core**: Company, Branch, Subscription, User
- **RBAC**: Role, Permission, PermissionCategory, RolePermission
- **Productos**: Product, Category, Recipe, RecipeItem
- **Operaciones**: Order, OrderAudit, OrderCounter, Inventory
- **Finanzas**: Payment, CashClosure
- **CRM**: Customer, CustomerAddress
- **Delivery**: DeliveryShift
- **Sistema**: PrintQueue

### Servicios (22 servicios)
- AuthService, RoleService, PermissionService
- ProductService, CategoryService, RecipeService
- OrderService, OrderStateMachine, OrderCounterService
- InventoryService, DeliveryService
- CustomerService, AddressService, RegistrationService
- PaymentService, CashService, ReportService
- NotificationService, PrintService, y más...

### Tecnologías
- **FastAPI** - Framework web moderno (async/await)
- **SQLModel** - ORM con Pydantic y type hints
- **PostgreSQL** - Base de datos relacional
- **Redis** - Caché y sesiones
- **Alembic** - Migraciones de BD
- **Docker** - Containerización
- **Pytest** - Testing framework

## 🔒 Seguridad

- JWT tokens con refresh
- Hashing bcrypt para passwords
- Decoradores `@require_permission` para validación automática
- Rate limiting
- CORS configurado
- Logs de seguridad estructurados
- Aislamiento multi-tenant verificado

## 📊 Monitoreo

- Health checks: `GET /health`
- Test de BD: `GET /bd-test`
- Logs JSON estructurados
- Métricas de performance

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

## 📖 Documentación Adicional

- `GUIA_APRENDIZAJE.md` - Roadmap de aprendizaje
- `SETUP_GUIDE.md` - Guía de instalación
- `PRM_PROYECTO_FASTOPS.md` - Documento de contexto del proyecto
- `INFORME_ESTADO_TESTING.md` - Estado actual de testing
- `docuemntos_de_desarrollo/` - Documentación técnica completa
  - `fastops_req_v3.md` - Requisitos del sistema
  - `fases de desarrollo.md` - Fases de desarrollo
  - `INFORME_CUMPLIMIENTO_REQUISITOS.md` - Cumplimiento de requisitos

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

**Última Actualización**: Enero 2026  
**Estado**: MVP en desarrollo activo - Módulos Core, CRM y Delivery implementados