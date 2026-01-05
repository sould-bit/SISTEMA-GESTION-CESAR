FastOps — Documento Maestro de Arquitectura y Desarrollo V4.0
Versión: 4.0 - Consolidación Final y Completa
Fecha: Enero 2026
Autor: Jhon (CEO) / Equipo de Desarrollo
Estado: Documento Definitivo para Ejecución
________________________________________
📋 ÍNDICE
1.	Información General del Proyecto
2.	Principios Arquitectónicos Fundamentales
3.	Arquitectura Técnica Completa
4.	Modelo de Datos Definitivo
5.	Sistema de Alto Rendimiento
6.	Endpoints API Completos
7.	WebSockets y Tiempo Real
8.	Seguridad Multi-Tenant
9.	PWA Cliente y Modificadores
10.	Sistema RBAC Avanzado
11.	Plan de Desarrollo por Fases
12.	Criterios de Calidad y Aceptación
13.	Infraestructura y Escalamiento
________________________________________
1. INFORMACIÓN GENERAL DEL PROYECTO
1.1 Visión del Sistema
FastOps es una plataforma SaaS multi-tenant de última generación para la gestión integral de salchipapererías y negocios de comida rápida, diseñada con principios de:
•	Arquitectura asíncrona: Sin bloqueos, respuestas < 1 segundo
•	Escalabilidad horizontal: De 1 a 1000+ negocios sin rediseño
•	Alta disponibilidad: 99.9% uptime con circuit breakers y fallbacks
•	Preparada para IA: Arquitectura extensible para módulos inteligentes
•	Multi-tenant nativo: Aislamiento total de datos por empresa
1.2 Objetivo Central
Eliminar completamente la dependencia de WhatsApp, papel y procesos manuales, digitalizando el 100% de las operaciones de un negocio de comida rápida con:
•	✅ Sistema de pedidos sin bloqueos (soporte para 100+ pedidos/hora)
•	✅ Inventario automático con recetas inteligentes
•	✅ Control de domiciliarios con GPS y asignación automática
•	✅ Reportes en tiempo real y auditoría completa
•	✅ PWA cliente para pedidos online con QR
•	✅ Sistema de caja con cierre automático
1.3 Modelo de Negocio SaaS
Planes de Suscripción:
Plan	Precio/mes	Sucursales	Usuarios	Productos	Características Extra
Trial	$0 (30 días)	1	3	50	-
Basic	$40.000 COP	1	5	200	Soporte email
Premium	$80.000 COP	Ilimitadas	Ilimitados	Ilimitados	Soporte prioritario + reportes avanzados
Enterprise	A consultar	Ilimitadas	Ilimitados	Ilimitados	IA + API + Soporte 24/7 + Onboarding
Proyección de Ingresos (50 clientes mix 50/50):
•	25 × $40.000 = $1.000.000 COP
•	25 × $80.000 = $2.000.000 COP
•	Total: $3.000.000 COP/mes
1.4 Usuarios del Sistema
1. Clientes Finales (PWA Pública)
•	Acceso vía QR code o link directo
•	Pedidos sin registro obligatorio
•	Personalización con modificadores (extras/exclusiones)
•	Seguimiento en tiempo real
•	Registro opcional para historial
2. Personal del Negocio (PWA Administrativa)
•	Administrador: Control total, configuración, reportes consolidados, gestión de sucursales
•	Cajero: Crear pedidos, recibir pagos, cierre de caja, asignar domiciliarios
•	Cocina: Ver comandas, actualizar estados, gestionar preparación
•	Domiciliario: App dedicada - recibir asignaciones, GPS, confirmar entregas
3. Super Admin (Panel Administrativo)
•	Gestión de todos los negocios registrados
•	Monitoreo de suscripciones y facturación
•	Soporte técnico centralizado
•	Análisis de performance de la plataforma
•	Gestión de planes y límites
________________________________________
2. PRINCIPIOS ARQUITECTÓNICOS FUNDAMENTALES
2.1 Principios No Negociables
✅ ASINCRONÍA OBLIGATORIA
REGLA: Ninguna operación debe bloquear el flujo principal
•	Respuesta al usuario SIEMPRE < 1 segundo
•	Procesamiento pesado en background workers
•	Cola de tareas con prioridades (high/normal/low)
•	Circuit breakers para prevenir cascadas de fallos
Ejemplo crítico:
python
# ❌ INCORRECTO (Bloquea la respuesta)
@router.post("/orders")
def create_order(order_data):
    order = db.create(order_data)
    print_order(order)  # Espera 5-10 segundos
    return order

# ✅ CORRECTO (Asíncrono)
@router.post("/orders")
async def create_order(order_data):
    order = await db.create(order_data)
    print_task.delay(order.id)  # Cola asíncrona
    return order  # Responde inmediatamente
```

#### ✅ CERO BLOQUEOS

- Sistema debe funcionar bajo alta carga (100+ pedidos/minuto)
- Manejo de concurrencia con locks optimistas
- Fallbacks automáticos en operaciones críticas
- Degradación elegante ante fallos

#### ✅ ESCALABILIDAD HORIZONTAL

- Arquitectura stateless (sin sesiones en memoria)
- Base de datos optimizada para multi-tenant
- Workers escalables independientemente
- CDN para contenido estático
- Redis para caché distribuido

#### ✅ EXTENSIBILIDAD FUTURA

**Preparado para:**
- Módulos de IA (chatbots, predicciones, recomendaciones)
- Integraciones con terceros (WhatsApp Business, Stripe, Rappi)
- Análisis avanzado con Machine Learning
- API pública para desarrolladores externos
- Sistema de plugins

#### ✅ RESILIENCIA

- Degradación elegante ante fallos
- Retry automático con backoff exponencial
- Logging estructurado para debugging
- Monitoreo proactivo con alertas
- Health checks en todos los servicios

### 2.2 Arquitectura de Referencia
```
┌────────────────────────────────────────────────────────────┐
│                  CAPA DE CLIENTES                          │
├────────────────────────────────────────────────────────────┤
│  PWA Cliente  │  PWA Admin   │  App Domiciliario         │
│  (React TS)   │  (React TS)  │  (React Native/PWA)       │
└────────┬───────┴──────┬───────┴──────────┬────────────────┘
         │              │                  │
         └──────────────┼──────────────────┘
                        │
         ┌──────────────▼────────────────┐
         │   API GATEWAY (FastAPI)       │
         │  - Rate Limiting              │
         │  - JWT Validation             │
         │  - Multi-Tenant Middleware    │
         │  - Circuit Breakers           │
         └──────────────┬────────────────┘
                        │
         ┌──────────────┴────────────────┐
         │                               │
    ┌────▼─────┐                  ┌─────▼──────┐
    │ REST API │                  │ WebSockets │
    │ Endpoints│                  │ (Socket.IO)│
    └────┬─────┘                  └──────┬─────┘
         │                               │
         └─────────────┬─────────────────┘
                       │
    ┌──────────────────▼─────────────────┐
    │      CAPA DE SERVICIOS             │
    │  - OrderService (async)            │
    │  - InventoryService (async)        │
    │  - PrintService (queue)            │
    │  - NotificationService (queue)     │
    │  - RBACService (cache)             │
    └──────────────────┬─────────────────┘
                       │
    ┌──────────────────┴─────────────────┐
    │                                    │
┌───▼────┐  ┌────────┐  ┌──────────────┐
│ Redis  │  │ Celery │  │ PostgreSQL   │
│ Cache  │  │ Workers│  │ Multi-Tenant │
└────────┘  └────────┘  └──────────────┘
________________________________________
3. ARQUITECTURA TÉCNICA COMPLETA
3.1 Stack Tecnológico Definitivo
Backend
yaml
Framework: FastAPI 0.104+
ORM: SQLModel 0.0.14+
Database: PostgreSQL 15+
Cache: Redis 7+
Queue: Celery + Redis
Auth: JWT (python-jose)
WebSockets: python-socketio
Validation: Pydantic v2
RBAC: Custom implementation con cache
Testing: pytest + pytest-asyncio + pytest-cov
Monitoring: Custom dashboard + Sentry
Frontend PWA Admin
yaml
Framework: React 18+ con TypeScript
State Management: Redux Toolkit + RTK Query
UI: TailwindCSS + shadcn/ui
Forms: React Hook Form + Zod
PWA: Workbox
Build: Vite
Testing: Vitest + React Testing Library
WebSockets: socket.io-client
PWA Cliente (Pedidos Online)
yaml
Framework: React 18 + TypeScript
State: Redux Toolkit (simplificado)
UI: TailwindCSS + componentes custom
Routing: React Router
Build: Vite
Offline: Service Worker + IndexedDB
App Móvil Domiciliarios
yaml
Opción 1: PWA avanzada (preferida para MVP)
Opción 2: React Native (Expo) para nativa
Maps: Google Maps API / Mapbox
GPS: Geolocation API
Networking: Axios + Socket.IO Client
Infraestructura
yaml
Backend Hosting: VPS (Contabo/Hetzner 4GB RAM)
Frontend Hosting: Vercel/Cloudflare Pages
Database: PostgreSQL en VPS
Cache/Queue: Redis en VPS
CDN: Cloudflare
Monitoring: Custom Dashboard + Sentry
CI/CD: GitHub Actions
Backups: Automated daily + S3
3.2 Patrones de Diseño Implementados
1. Repository Pattern
python
class OrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, order: OrderCreate) -> Order:
        """Crear pedido con validación de company_id"""
        
    async def get_by_id(self, order_id: int, company_id: int) -> Order | None:
        """Obtener con filtro automático multi-tenant"""
        
    async def list_by_branch(
        self, 
        company_id: int,
        branch_id: int,
        filters: OrderFilters
    ) -> list[Order]:
        """Listar con filtros complejos"""
2. Service Layer Pattern
python
class OrderService:
    def __init__(
        self,
        repo: OrderRepository,
        queue: TaskQueue,
        inventory: InventoryService
    ):
        self.repo = repo
        self.queue = queue
        self.inventory = inventory
    
    async def create_order(
        self, 
        order: OrderCreate,
        user: User
    ) -> OrderResponse:
        """
        Flujo completo de creación:
        1. Validar stock disponible
        2. Generar consecutivo único
        3. Crear orden en BD (transacción)
        4. Encolar impresión
        5. Notificar WebSocket
        6. Retornar inmediatamente
        """
        # Implementación...
3. Circuit Breaker Pattern
python
@circuit_breaker(failure_threshold=5, timeout=60)
async def print_order(order_id: int):
    """
    Intenta imprimir, si falla 5 veces consecutivas:
    - Abre el circuito
    - Activa fallback (pantalla/email)
    - Alerta al administrador
    """
4. CQRS (Command Query Responsibility Segregation)
python
# Comandos (Escritura)
class OrderCommands:
    async def create_order(...) -> Order
    async def update_status(...) -> Order
    async def assign_delivery(...) -> Order

# Consultas (Lectura - con cache)
class OrderQueries:
    @cached(ttl=30)
    async def get_order(...) -> Order
    
    @cached(ttl=60)
    async def list_orders(...) -> list[Order]
5. Decorator Pattern (RBAC)
python
@router.get("/admin/reports")
@require_permission("reports.view")
@require_active_subscription
async def get_reports(
    current_user: User = Depends(get_current_user)
):
    """Decoradores apilables para seguridad"""
________________________________________
4. MODELO DE DATOS DEFINITIVO
4.1 Diagrama Entidad-Relación Multi-Tenant
mermaid
erDiagram
    COMPANIES ||--o{ BRANCHES : tiene
    COMPANIES ||--o{ SUBSCRIPTIONS : tiene
    COMPANIES ||--o{ USERS : emplea
    COMPANIES ||--o{ PRODUCTS : vende
    COMPANIES ||--o{ ROLES : define
    
    BRANCHES ||--o{ USERS : asigna
    BRANCHES ||--o{ ORDERS : recibe
    BRANCHES ||--o{ INVENTORY_ITEMS : maneja
    BRANCHES ||--o{ CASH_CLOSURES : registra
    
    ORDERS ||--|{ ORDER_ITEMS : contiene
    ORDERS ||--o{ PAYMENTS : registra
    ORDERS }o--|| USERS : creado_por
    ORDERS }o--o| USERS : domiciliario
    
    ORDER_ITEMS ||--o{ ORDER_ITEM_MODIFIERS : tiene
    
    PRODUCTS ||--|| RECIPES : tiene
    PRODUCTS ||--o{ PRODUCT_MODIFIERS : permite
    
    RECIPES ||--|{ RECIPE_ITEMS : requiere
    RECIPE_ITEMS }o--|| INVENTORY_ITEMS : usa
    
    INVENTORY_ITEMS ||--o{ INVENTORY_MOVEMENTS : registra
    
    ROLES ||--o{ ROLE_PERMISSIONS : tiene
    ROLE_PERMISSIONS }o--|| PERMISSIONS : referencia
    USERS }o--|| ROLES : tiene
4.2 Tablas Multi-Tenant Core
companies
sql
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    legal_name VARCHAR(200),
    tax_id VARCHAR(50),
    owner_name VARCHAR(200) NOT NULL,
    owner_email VARCHAR(200) UNIQUE NOT NULL,
    owner_phone VARCHAR(50),
    plan VARCHAR(20) NOT NULL DEFAULT 'trial',
    is_active BOOLEAN NOT NULL DEFAULT true,
    trial_ends_at TIMESTAMP,
    timezone VARCHAR(50) DEFAULT 'America/Bogota',
    currency VARCHAR(3) DEFAULT 'COP',
    
    -- Límites por plan
    max_users INTEGER,
    max_branches INTEGER,
    max_products INTEGER,
    
    -- Configuración del negocio
    logo_url VARCHAR(500),
    primary_color VARCHAR(7),
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP
);

CREATE INDEX idx_companies_slug ON companies(slug);
CREATE INDEX idx_companies_active ON companies(is_active);
CREATE INDEX idx_companies_plan ON companies(plan, is_active);
branches
sql
CREATE TABLE branches (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    name VARCHAR(200) NOT NULL,
    code VARCHAR(20) NOT NULL,
    
    -- Ubicación
    address TEXT,
    phone VARCHAR(50),
    latitude NUMERIC(10,8),
    longitude NUMERIC(11,8),
    
    -- Estado
    is_active BOOLEAN DEFAULT true,
    is_main BOOLEAN DEFAULT false,
    
    -- Horarios (JSON)
    business_hours JSONB,
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(company_id, code)
);

CREATE INDEX idx_branches_company ON branches(company_id);
CREATE INDEX idx_branches_active ON branches(company_id, is_active);
CREATE INDEX idx_branches_location ON branches(latitude, longitude);
subscriptions
sql
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    plan VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    
    -- Períodos
    started_at TIMESTAMP NOT NULL,
    current_period_start TIMESTAMP NOT NULL,
    current_period_end TIMESTAMP NOT NULL,
    cancelled_at TIMESTAMP,
    
    -- Facturación
    amount NUMERIC(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'COP',
    
    -- Integraciones de pago (futuro)
    stripe_subscription_id VARCHAR(100),
    wompi_subscription_id VARCHAR(100),
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_subscriptions_company ON subscriptions(company_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status, current_period_end);
CREATE INDEX idx_subscriptions_period ON subscriptions(current_period_end) 
    WHERE status = 'active';
order_counters
sql
CREATE TABLE order_counters (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    branch_id INTEGER NOT NULL REFERENCES branches(id),
    order_type VARCHAR(20) NOT NULL,
    last_number INTEGER NOT NULL DEFAULT 0,
    
    -- Para reset anual/mensual (opcional)
    period VARCHAR(10),
    
    UNIQUE(company_id, branch_id, order_type, period)
);

CREATE INDEX idx_order_counters ON order_counters(company_id, branch_id, order_type);
4.3 Tablas de Usuarios y Seguridad
users
sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    branch_id INTEGER REFERENCES branches(id),
    role_id INTEGER REFERENCES roles(id),
    
    -- Credenciales
    username VARCHAR(100) NOT NULL,
    email VARCHAR(200),
    full_name VARCHAR(200) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    
    -- Estado
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    
    UNIQUE(company_id, username)
);

CREATE INDEX idx_users_company ON users(company_id);
CREATE INDEX idx_users_branch ON users(branch_id);
CREATE INDEX idx_users_login ON users(company_id, username, is_active);
CREATE INDEX idx_users_role ON users(role_id);
roles
sql
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Jerarquía
    level INTEGER NOT NULL DEFAULT 0,
    
    -- Estado
    is_active BOOLEAN DEFAULT true,
    is_system BOOLEAN DEFAULT false,
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    
    UNIQUE(company_id, name)
);

CREATE INDEX idx_roles_company ON roles(company_id);
CREATE INDEX idx_roles_active ON roles(company_id, is_active);
permissions
sql
CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES permission_categories(id),
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    
    -- Estado
    is_active BOOLEAN DEFAULT true,
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(resource, action)
);

CREATE INDEX idx_permissions_resource ON permissions(resource);
CREATE INDEX idx_permissions_category ON permissions(category_id);
permission_categories
sql
CREATE TABLE permission_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    icon VARCHAR(50),
    sort_order INTEGER DEFAULT 0
);
role_permissions
sql
CREATE TABLE role_permissions (
    id SERIAL PRIMARY KEY,
    role_id INTEGER NOT NULL REFERENCES roles(id),
    permission_id INTEGER NOT NULL REFERENCES permissions(id),
    
    -- Auditoría
    granted_at TIMESTAMP DEFAULT NOW(),
    granted_by INTEGER REFERENCES users(id),
    
    UNIQUE(role_id, permission_id)
);

CREATE INDEX idx_role_permissions_role ON role_permissions(role_id);
CREATE INDEX idx_role_permissions_permission ON role_permissions(permission_id);
4.4 Tablas de Productos y Catálogo
categories
sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    
    -- Visualización
    icon VARCHAR(100),
    color VARCHAR(7),
    sort_order INTEGER DEFAULT 0,
    
    -- Estado
    is_active BOOLEAN DEFAULT true,
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(company_id, name)
);

CREATE INDEX idx_categories_company ON categories(company_id);
CREATE INDEX idx_categories_active ON categories(company_id, is_active);
CREATE INDEX idx_categories_sort ON categories(company_id, sort_order);
products
sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    category_id INTEGER REFERENCES categories(id),
    
    -- Información básica
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price NUMERIC(12,2) NOT NULL,
    
    -- Media
    image_url VARCHAR(500),
    images JSONB, -- Array de imágenes
    
    -- Configuración
    allow_modifiers BOOLEAN DEFAULT true,
    preparation_time INTEGER, -- minutos
    
    -- Estado
    is_active BOOLEAN DEFAULT true,
    is_featured BOOLEAN DEFAULT false,
    
    -- SEO (para PWA cliente)
    slug VARCHAR(200),
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(company_id, slug)
);

CREATE INDEX idx_products_company ON products(company_id);
CREATE INDEX idx_products_category ON products(company_id, category_id);
CREATE INDEX idx_products_active ON products(company_id, is_active);
CREATE INDEX idx_products_featured ON products(company_id, is_featured, is_active);
CREATE INDEX idx_products_slug ON products(company_id, slug);
product_modifiers
sql
CREATE TABLE product_modifiers (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    
    -- Información del modificador
    name VARCHAR(200) NOT NULL,
    modifier_type VARCHAR(20) NOT NULL, -- 'addition' o 'exclusion'
    price NUMERIC(12,2) DEFAULT 0,
    
    -- Configuración
    max_quantity INTEGER DEFAULT 1,
    is_required BOOLEAN DEFAULT false,
    
    -- Estado
    is_available BOOLEAN DEFAULT true,
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_product_modifiers_product ON product_modifiers(product_id);
CREATE INDEX idx_product_modifiers_type ON product_modifiers(product_id, modifier_type);
CREATE INDEX idx_product_modifiers_available ON product_modifiers(product_id, is_available);
4.5 Tablas de Pedidos
orders
sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    branch_id INTEGER NOT NULL REFERENCES branches(id),
    
    -- Identificación
    consecutive VARCHAR(50) NOT NULL,
    order_type VARCHAR(20) NOT NULL, -- mesa, llevar, domicilio
    
    -- Datos del pedido
    table_number VARCHAR(20),
    customer_name VARCHAR(200),
    customer_phone VARCHAR(50),
    customer_email VARCHAR(200),
    delivery_address TEXT,
    delivery_notes TEXT,
    
    -- Ubicación (para domicilios)
    delivery_latitude NUMERIC(10,8),
    delivery_longitude NUMERIC(11,8),
    
    -- Estado y seguimiento
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    
    -- Montos
    subtotal NUMERIC(12,2) NOT NULL,
    delivery_fee NUMERIC(12,2) DEFAULT 0,
    total NUMERIC(12,2) NOT NULL,
    
    -- Asignación
    delivery_person_id INTEGER REFERENCES users(id),
    assigned_at TIMESTAMP,
    
    -- Tiempos
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    ready_at TIMESTAMP,
    delivered_at TIMESTAMP,
    
    -- Cancelación
    cancelled_at TIMESTAMP,
    cancellation_reason TEXT,
    
    UNIQUE(company_id, consecutive)
);

CREATE INDEX idx_orders_company_branch ON orders(company_id, branch_id);
CREATE INDEX idx_orders_status ON orders(company_id, status, created_at);
CREATE INDEX idx_orders_consecutive ON orders(company_id, consecutive);
CREATE INDEX idx_orders_delivery ON orders(delivery_person_id, status);
CREATE INDEX idx_orders_customer_phone ON orders(company_id, customer_phone);
CREATE INDEX idx_orders_created ON orders(created_at);
order_items
sql
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    
    -- Cantidad y precios
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12,2) NOT NULL,
    subtotal NUMERIC(12,2) NOT NULL,
    
    -- Notas especiales
    notes TEXT,
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);
order_item_modifiers
sql
CREATE TABLE order_item_modifiers (
    id SERIAL PRIMARY KEY,
    order_item_id INTEGER NOT NULL REFERENCES order_items(id) ON DELETE CASCADE,
    modifier_id INTEGER NOT NULL REFERENCES product_modifiers(id),
    
    -- Cantidad y precio
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price NUMERIC(12,2) NOT NULL,
    subtotal NUMERIC(12,2) NOT NULL,
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_order_item_modifiers_item ON order_item_modifiers(order_item_id);
CREATE INDEX idx_order_item_modifiers_modifier ON order_item_modifiers(modifier_id);
payments
sql
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    
    -- Método de pago
    payment_method VARCHAR(20) NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    
    -- Referencia (transacción)
    reference VARCHAR(200),
    
    -- Estado
    status VARCHAR(20) DEFAULT 'completed',
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id)
);

CREATE INDEX idx_payments_order ON payments(order_id);
CREATE INDEX idx_payments_method ON payments(payment_method, created_at);
CREATE INDEX idx_payments_created ON payments(created_at);
4.6 Tablas de Inventario
inventory_items
sql
CREATE TABLE inventory_items (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    branch_id INTEGER REFERENCES branches(id),
    
    -- Información del insumo
    name VARCHAR(200) NOT NULL,
    unit_of_measure VARCHAR(50) NOT NULL,
    
    -- Stock
    current_stock NUMERIC(12,4) NOT NULL DEFAULT 0,
    min_stock NUMERIC(12,4),
    max_stock NUMERIC(12,4),
    
    -- Costos
    average_cost NUMERIC(12,4),
    last_purchase_cost NUMERIC(12,4),
    
    -- Estado
    is_active BOOLEAN DEFAULT true,
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_inventory_company ON inventory_items(company_id);
CREATE INDEX idx_inventory_branch ON inventory_items(branch_id);
CREATE INDEX idx_inventory_stock ON inventory_items(company_id, current_stock, min_stock);
CREATE INDEX idx_inventory_active ON inventory_items(company_id, is_active);
recipes
sql
CREATE TABLE recipes (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    
    -- Información
    description TEXT,
    preparation_notes TEXT,
Continuar
4 ene
-- Costos calculados total_cost NUMERIC(12,4),
-- Auditoría
created_at TIMESTAMP DEFAULT NOW(),
updated_at TIMESTAMP DEFAULT NOW(),

UNIQUE(product_id)
);
CREATE INDEX idx_recipes_company ON recipes(company_id); CREATE INDEX idx_recipes_product ON recipes(product_id);

#### `recipe_items`
```sql
CREATE TABLE recipe_items (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    inventory_item_id INTEGER NOT NULL REFERENCES inventory_items(id),
    
    -- Cantidad requerida
    quantity NUMERIC(12,4) NOT NULL,
    
    -- Costo al momento (cache)
    unit_cost NUMERIC(12,4),
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_recipe_items_recipe ON recipe_items(recipe_id);
CREATE INDEX idx_recipe_items_inventory ON recipe_items(inventory_item_id);
```

#### `inventory_movements`
```sql
CREATE TABLE inventory_movements (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    branch_id INTEGER NOT NULL REFERENCES branches(id),
    inventory_item_id INTEGER NOT NULL REFERENCES inventory_items(id),
    
    -- Tipo de movimiento
    movement_type VARCHAR(20) NOT NULL, -- entrada, salida, ajuste
    quantity NUMERIC(12,4) NOT NULL,
    
    -- Costos
    unit_cost NUMERIC(12,4),
    total_cost NUMERIC(12,4),
    
    -- Razón y referencia
    reason VARCHAR(200),
    reference VARCHAR(200), -- ID de pedido o nota
    
    -- Auditoría
    user_id INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_movements_company_branch ON inventory_movements(company_id, branch_id);
CREATE INDEX idx_movements_item ON inventory_movements(inventory_item_id);
CREATE INDEX idx_movements_date ON inventory_movements(company_id, created_at);
CREATE INDEX idx_movements_type ON inventory_movements(movement_type, created_at);
```

### 4.7 Tablas de Caja y Reportes

#### `cash_closures`
```sql
CREATE TABLE cash_closures (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    branch_id INTEGER NOT NULL REFERENCES branches(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    -- Montos
    expected_total NUMERIC(12,2) NOT NULL,
    actual_total NUMERIC(12,2) NOT NULL,
    difference NUMERIC(12,2) NOT NULL,
    
    -- Desglose por método de pago (JSON)
    payment_breakdown JSONB,
    
    -- Período
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    
    -- Notas
    notes TEXT,
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_closures_company_branch ON cash_closures(company_id, branch_id);
CREATE INDEX idx_closures_date ON cash_closures(company_id, created_at);
CREATE INDEX idx_closures_user ON cash_closures(user_id, created_at);
```

### 4.8 Tablas de Sistema de Impresión

#### `print_queue`
```sql
CREATE TABLE print_queue (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    branch_id INTEGER NOT NULL REFERENCES branches(id),
    order_id INTEGER NOT NULL REFERENCES orders(id),
    
    -- Prioridad
    priority VARCHAR(20) NOT NULL DEFAULT 'normal',
    
    -- Estado
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    
    -- Configuración de impresora
    printer_id VARCHAR(50),
    
    -- Payload de impresión
    payload JSONB NOT NULL,
    
    -- Error handling
    error_message TEXT,
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_print_queue_status ON print_queue(company_id, branch_id, status, priority);
CREATE INDEX idx_print_queue_created ON print_queue(created_at);
CREATE INDEX idx_print_queue_order ON print_queue(order_id);
```

### 4.9 Tablas de Auditoría

#### `audit_logs`
```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    branch_id INTEGER REFERENCES branches(id),
    user_id INTEGER REFERENCES users(id),
    
    -- Acción
    action VARCHAR(100) NOT NULL,
    entity VARCHAR(100) NOT NULL,
    entity_id INTEGER,
    
    -- Detalles (JSON)
    details JSONB,
    
    -- Request info
    ip_address VARCHAR(50),
    user_agent TEXT,
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_logs_company ON audit_logs(company_id, created_at);
CREATE INDEX idx_logs_user ON audit_logs(user_id, created_at);
CREATE INDEX idx_logs_entity ON audit_logs(company_id, entity, entity_id);
CREATE INDEX idx_logs_action ON audit_logs(action, created_at);
```

### 4.10 Tablas de Domiciliarios

#### `delivery_person_locations`
```sql
CREATE TABLE delivery_person_locations (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    delivery_person_id INTEGER NOT NULL REFERENCES users(id),
    
    -- Ubicación GPS
    latitude NUMERIC(10,8) NOT NULL,
    longitude NUMERIC(11,8) NOT NULL,
    accuracy NUMERIC(6,2),
    
    -- Contexto
    order_id INTEGER REFERENCES orders(id),
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_delivery_locations_person ON delivery_person_locations(delivery_person_id, created_at);
CREATE INDEX idx_delivery_locations_order ON delivery_person_locations(order_id);
CREATE INDEX idx_delivery_locations_coords ON delivery_person_locations(latitude, longitude);
```

#### `delivery_person_status`
```sql
CREATE TABLE delivery_person_status (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    delivery_person_id INTEGER NOT NULL REFERENCES users(id),
    
    -- Estado
    status VARCHAR(20) NOT NULL, -- disponible, en_ruta, entregando, en_negocio
    
    -- Auditoría
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(delivery_person_id)
);

CREATE INDEX idx_delivery_status_company ON delivery_person_status(company_id, status);
CREATE INDEX idx_delivery_status_person ON delivery_person_status(delivery_person_id);
```

---

## 5. SISTEMA DE ALTO RENDIMIENTO

### 5.1 Cola de Impresión Asíncrona

**Problema resuelto:** Sistema anterior tardaba 30 minutos en imprimir comandas en días de alta carga (120+ pedidos/día).

**Solución arquitectural:**
Cliente → Backend (< 1s) → Redis Queue → Workers (2-10) → Impresoras ↓ Respuesta inmediata

#### Implementación con Celery
```python
# backend/app/tasks/printing.py
from celery import Celery
from app.services.printer import PrinterService

celery_app = Celery('fastops', broker='redis://localhost:6379/0')

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Bogota',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30,
    task_soft_time_limit=25,
)

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=2
)
def print_order_task(
    self, 
    order_id: int, 
    company_id: int, 
    branch_id: int
):
    """
    Task asíncrona para imprimir comanda
    """
    try:
        printer_service = PrinterService()
        result = printer_service.print_order(
            order_id=order_id,
            company_id=company_id,
            branch_id=branch_id
        )
        
        # Actualizar estado en print_queue
        update_print_queue_status(order_id, 'completed')
        
        # Notificar por WebSocket
        emit_print_completed(order_id, branch_id)
        
        return result
        
    except PrinterOfflineException as exc:
        # Activar fallback
        activate_fallback(order_id, company_id, branch_id)
        raise self.retry(exc=exc, countdown=5)
        
    except Exception as exc:
        # Log detallado
        logger.error(f"Print error: {exc}", extra={
            "order_id": order_id,
            "company_id": company_id,
            "attempt": self.request.retries
        })
        
        if self.request.retries >= self.max_retries:
            # Fallback definitivo
            activate_fallback(order_id, company_id, branch_id)
        
        raise self.retry(exc=exc)
```

#### Endpoint de creación de pedido (NO bloqueante)
```python
# backend/app/routers/orders.py
@router.post("/orders", response_model=OrderResponse)
async def create_order(
    order: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Crear pedido - Respuesta < 1 segundo garantizada
    
    Flujo:
    1. Validar datos (100ms)
    2. Crear en BD con transacción (300-500ms)
    3. Encolar impresión (50ms)
    4. Notificar WebSocket (50ms)
    5. RETORNAR (total < 1s)
    """
    
    # 1. Validaciones rápidas
    await order_service.validate_order(order, current_user, db)
    
    # 2. Crear pedido en BD (transacción atómica)
    created_order = await order_service.create(
        order=order,
        user=current_user,
        db=db
    )
    
    # 3. Encolar impresión (NO BLOQUEANTE)
    print_order_task.delay(
        order_id=created_order.id,
        company_id=current_user.company_id,
        branch_id=current_user.branch_id
    )
    
    # 4. Notificar por WebSocket (NO BLOQUEANTE)
    await socketio.emit(
        'order:created',
        {
            'order_id': created_order.id,
            'consecutive': created_order.consecutive,
            'total': float(created_order.total),
            'items': [item.dict() for item in created_order.items]
        },
        room=f"kitchen_{current_user.company_id}_{current_user.branch_id}"
    )
    
    # 5. RESPUESTA INMEDIATA
    return OrderResponse(
        id=created_order.id,
        consecutive=created_order.consecutive,
        status="received",
        total=created_order.total,
        print_status="queued",
        estimated_print_time="5-10 segundos"
    )
```

### 5.2 Workers Escalables

#### Configuración dinámica:
```python
# backend/app/workers/config.py
class WorkerConfig:
    MIN_WORKERS = 2
    MAX_WORKERS = 10
    SCALE_UP_THRESHOLD = 15    # pedidos en cola
    SCALE_DOWN_THRESHOLD = 5
    
    @classmethod
    def calculate_workers(cls, queue_size: int) -> int:
        """
        Calcula número óptimo de workers según carga
        """
        if queue_size > cls.SCALE_UP_THRESHOLD:
            return min(cls.MAX_WORKERS, queue_size // 5)
        elif queue_size < cls.SCALE_DOWN_THRESHOLD:
            return cls.MIN_WORKERS
        return None  # No cambiar

    @classmethod
    async def auto_scale(cls, redis_client):
        """
        Auto-scaling basado en métricas
        """
        queue_size = await redis_client.llen('celery')
        workers_needed = cls.calculate_workers(queue_size)
        
        if workers_needed:
            await adjust_workers(workers_needed)
```

#### Comandos de inicio:
```bash
# Desarrollo (2 workers)
celery -A app.tasks.celery_app worker \
  --loglevel=info \
  --concurrency=2 \
  --hostname=worker1@%h

# Producción (auto-scale 2-10 workers)
celery -A app.tasks.celery_app worker \
  --loglevel=info \
  --autoscale=10,2 \
  --max-tasks-per-child=100 \
  --hostname=worker-prod@%h
```

### 5.3 Circuit Breaker para Impresoras
```python
# backend/app/core/circuit_breaker.py
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Any

class CircuitState(Enum):
    CLOSED = "closed"         # Normal
    OPEN = "open"             # Impresora caída
    HALF_OPEN = "half_open"   # Probando

class CircuitBreaker:
    def __init__(
        self, 
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.last_failure_time = None
        self.success_count = 0
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Ejecuta función protegida por circuit breaker
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker: attempting reset")
            else:
                raise CircuitBreakerOpen(
                    "Printer unavailable - circuit breaker open"
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Resetear contadores en éxito"""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 3:
                self.state = CircuitState.CLOSED
                self.success_count = 0
                logger.info("Circuit breaker: closed after recovery")
    
    def _on_failure(self):
        """Incrementar fallos y abrir circuito si necesario"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.success_count = 0
            logger.error(f"Circuit breaker: opened after {self.failure_count} failures")
            
            # Activar fallback automático
            self._activate_fallback()
    
    def _should_attempt_reset(self) -> bool:
        """Verificar si es momento de intentar resetear"""
        if not self.last_failure_time:
            return True
        
        elapsed = (datetime.now() - self.last_failure_time).seconds
        return elapsed >= self.timeout
    
    def _activate_fallback(self):
        """Activar sistema de fallback"""
        from app.services.print_fallback import PrintFallbackService
        
        fallback = PrintFallbackService()
        fallback.notify_admin_critical()
        fallback.enable_screen_mode()

class CircuitBreakerOpen(Exception):
    """Excepción cuando el circuito está abierto"""
    pass
```

### 5.4 Sistema de Fallback
```python
# backend/app/services/print_fallback.py
from typing import Dict, Any
import asyncio

class PrintFallbackService:
    """
    Métodos alternativos cuando la impresora falla
    """
    
    def __init__(self):
        self.socketio = get_socketio_instance()
        self.email_service = EmailService()
    
    async def display_on_kitchen_screen(
        self, 
        order_data: Dict[str, Any]
    ):
        """
        Mostrar pedido en pantalla de cocina como fallback
        """
        await self.socketio.emit(
            'print:fallback',
            {
                'order': order_data,
                'message': '⚠️ IMPRIMIR MANUALMENTE',
                'alert': True,
                'priority': 'high'
            },
            room=f"kitchen_{order_data['company_id']}_{order_data['branch_id']}"
        )
        
        logger.warning(
            "Print fallback activated - screen mode",
            extra=order_data
        )
    
    async def generate_pdf_backup(
        self, 
        order_data: Dict[str, Any]
    ) -> str:
        """
        Generar PDF de respaldo
        """
        from app.services.pdf_generator import PDFGenerator
        
        pdf_path = await PDFGenerator.create_order_pdf(order_data)
        
        # Notificar que PDF está listo
        await self.socketio.emit(
            'pdf:ready',
            {'order_id': order_data['id'], 'pdf_url': pdf_path},
            room=f"admin_{order_data['company_id']}"
        )
        
        return pdf_path
    
    async def send_email_emergency(
        self, 
        order_data: Dict[str, Any],
        recipient: str
    ):
        """
        Enviar email de emergencia con detalles del pedido
        """
        await self.email_service.send(
            to=recipient,
            subject=f"🚨 URGENTE: Pedido {order_data['consecutive']}",
            template="emergency_order",
            context={
                'order': order_data,
                'reason': 'Impresora fuera de servicio'
            }
        )
    
    async def notify_admin_critical(self):
        """
        Alertar al administrador sobre fallo crítico
        """
        await self.socketio.emit(
            'system:alert',
            {
                'type': 'printer_failure',
                'severity': 'critical',
                'message': 'Sistema de impresión fuera de servicio',
                'action_required': True,
                'timestamp': datetime.now().isoformat()
            },
            room='admins'
        )
    
    def enable_screen_mode(self):
        """
        Activar modo de pantalla para todas las órdenes
        """
        # Actualizar configuración global
        set_config('print_mode', 'screen')
        
        logger.info("Print mode switched to SCREEN due to printer failure")
```

### 5.5 Monitoreo de Performance
```python
# backend/app/routers/monitoring.py
@router.get("/admin/performance/dashboard")
async def performance_dashboard(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Dashboard completo de performance en tiempo real
    """
    
    # 1. Estado de la cola de impresión
    queue_stats = await get_queue_statistics(
        company_id=current_user.company_id,
        db=db
    )
    
    # 2. Workers activos
    celery_inspect = celery_app.control.inspect()
    active_workers = len(celery_inspect.active() or {})
    active_tasks = celery_inspect.active() or {}
    
    # 3. Tiempo promedio de procesamiento
    avg_time = await calculate_avg_processing_time(
        company_id=current_user.company_id,
        last_hours=1,
        db=db
    )
    
    # 4. Circuit breakers status
    circuit_status = {
        printer_id: {
            'state': cb.state.value,
            'failures': cb.failure_count,
            'last_failure': cb.last_failure_time.isoformat() 
                if cb.last_failure_time else None
        }
        for printer_id, cb in circuit_breakers.items()
    }
    
    # 5. Métricas de sistema
    system_metrics = {
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent
    }
    
    # 6. Alertas activas
    alerts = await get_active_alerts(current_user.company_id)
    
    return {
        "queue": {
            "pending": queue_stats['pending'],
            "processing": queue_stats['processing'],
            "failed": queue_stats['failed'],
            "avg_wait_time": queue_stats['avg_wait_time']
        },
        "workers": {
            "active": active_workers,
            "target": WorkerConfig.MIN_WORKERS,
            "tasks": sum(len(tasks) for tasks in active_tasks.values())
        },
        "performance": {
            "avg_processing_time_seconds": round(avg_time, 2),
            "target_seconds": 5.0,
            "status": "good" if avg_time < 10 else "warning"
        },
        "circuit_breakers": circuit_status,
        "system": system_metrics,
        "alerts": alerts,
        "timestamp": datetime.now().isoformat()
    }
```

---

## 6. ENDPOINTS API COMPLETOS

### 6.1 Autenticación y Autorización
POST /api/v1/auth/register # Registro nuevo negocio (self-service) POST /api/v1/auth/login # Login (JWT con company_id y branch_id) POST /api/v1/auth/refresh # Renovar token GET /api/v1/auth/me # Datos del usuario actual POST /api/v1/auth/switch-branch # Cambiar sucursal (admins) POST /api/v1/auth/logout # Cerrar sesión POST /api/v1/auth/forgot-password # Recuperar contraseña POST /api/v1/auth/reset-password # Resetear contraseña POST /api/v1/auth/verify-email # Verificar email POST /api/v1/auth/resend-verification # Reenviar verificación

### 6.2 Gestión de Negocios (Super Admin)
GET /api/v1/admin/companies # Listar todos los negocios POST /api/v1/admin/companies # Crear negocio manualmente GET /api/v1/admin/companies/{id} # Detalle de negocio PUT /api/v1/admin/companies/{id} # Actualizar negocio DELETE /api/v1/admin/companies/{id} # Desactivar negocio POST /api/v1/admin/companies/{id}/activate # Reactivar negocio GET /api/v1/admin/companies/{id}/stats # Estadísticas del negocio GET /api/v1/admin/dashboard # Dashboard super admin

### 6.3 Gestión de Sucursales
GET /api/v1/branches # Listar sucursales del negocio POST /api/v1/branches # Crear nueva sucursal GET /api/v1/branches/{id} # Detalle de sucursal PUT /api/v1/branches/{id} # Actualizar sucursal DELETE /api/v1/branches/{id} # Eliminar sucursal GET /api/v1/branches/{id}/stats # Estadísticas de sucursal PUT /api/v1/branches/{id}/hours # Actualizar horarios

### 6.4 Suscripciones
GET /api/v1/subscriptions/current # Suscripción actual GET /api/v1/subscriptions/plans # Planes disponibles POST /api/v1/subscriptions/upgrade # Cambiar a plan superior POST /api/v1/subscriptions/downgrade # Cambiar a plan inferior POST /api/v1/subscriptions/cancel # Cancelar suscripción GET /api/v1/subscriptions/invoices # Historial de facturas POST /api/v1/subscriptions/payment-method # Actualizar método de pago GET /api/v1/subscriptions/usage # Uso actual vs límites

### 6.5 Usuarios y Roles (RBAC)
Usuarios
GET /api/v1/users # Listar usuarios POST /api/v1/users # Crear usuario GET /api/v1/users/{id} # Detalle de usuario PUT /api/v1/users/{id} # Actualizar usuario DELETE /api/v1/users/{id} # Eliminar usuario PUT /api/v1/users/{id}/role # Cambiar rol PUT /api/v1/users/{id}/branch # Cambiar sucursal
Roles
GET /api/v1/rbac/roles # Listar roles POST /api/v1/rbac/roles # Crear rol GET /api/v1/rbac/roles/{id} # Detalle con permisos PUT /api/v1/rbac/roles/{id} # Actualizar rol DELETE /api/v1/rbac/roles/{id} # Eliminar rol POST /api/v1/rbac/roles/{id}/permissions/{pid} # Asignar permiso DELETE /api/v1/rbac/roles/{id}/permissions/{pid} # Revocar permiso
Permisos
GET /api/v1/rbac/permissions # Listar permisos GET /api/v1/rbac/permissions/categories # Categorías de permisos GET /api/v1/rbac/my-permissions # Permisos del usuario actual

### 6.6 Productos y Catálogo
Categorías
GET /api/v1/categories # Listar categorías POST /api/v1/categories # Crear categoría PUT /api/v1/categories/{id} # Actualizar categoría DELETE /api/v1/categories/{id} # Eliminar categoría PUT /api/v1/categories/reorder # Reordenar categorías
Productos
GET /api/v1/products # Listar productos POST /api/v1/products # Crear producto GET /api/v1/products/{id} # Detalle de producto PUT /api/v1/products/{id} # Actualizar producto DELETE /api/v1/products/{id} # Eliminar producto POST /api/v1/products/{id}/image # Subir imagen POST /api/v1/products/bulk-import # Importación masiva
Recetas
POST /api/v1/products/{id}/recipe # Crear/actualizar receta GET /api/v1/products/{id}/recipe # Ver receta DELETE /api/v1/products/{id}/recipe # Eliminar receta GET /api/v1/products/{id}/cost # Calcular costo
Modificadores
GET /api/v1/products/{id}/modifiers # Listar modificadores POST /api/v1/products/{id}/modifiers # Crear modificador PUT /api/v1/modifiers/{id} # Actualizar modificador DELETE /api/v1/modifiers/{id} # Eliminar modificador

### 6.7 Pedidos (Asíncronos)
POST /api/v1/orders # Crear pedido (< 1s respuesta) GET /api/v1/orders # Listar pedidos GET /api/v1/orders/{id} # Detalle de pedido PATCH /api/v1/orders/{id}/status # Cambiar estado POST /api/v1/orders/{id}/assign # Asignar domiciliario POST /api/v1/orders/{id}/cancel # Cancelar pedido POST /api/v1/orders/{id}/reprint # Reenviar a cola de impresión GET /api/v1/orders/stats # Estadísticas de pedidos GET /api/v1/orders/{id}/timeline # Timeline del pedido

### 6.8 Cocina
GET /api/v1/kitchen/orders # Pedidos por preparar POST /api/v1/kitchen/orders/{id}/start # Iniciar preparación POST /api/v1/kitchen/orders/{id}/ready # Marcar como listo GET /api/v1/kitchen/stats # Estadísticas de cocina GET /api/v1/kitchen/queue # Cola de preparación

### 6.9 Inventario
Insumos
GET /api/v1/inventory # Listar inventario POST /api/v1/inventory/items # Crear insumo PUT /api/v1/inventory/items/{id} # Actualizar insumo DELETE /api/v1/inventory/items/{id} # Eliminar insumo GET /api/v1/inventory/low-stock # Alertas de stock bajo
Movimientos
POST /api/v1/inventory/movements # Registrar movimiento GET /api/v1/inventory/movements # Historial de movimientos POST /api/v1/inventory/bulk-import # Importación masiva GET /api/v1/inventory/report # Reporte de inventario GET /api/v1/inventory/kardex/{id} # Kardex de insumo

### 6.10 Domiciliarios
Autenticación
POST /api/v1/delivery/login # Login domiciliario
Gestión
GET /api/v1/delivery/me # Datos del domiciliario GET /api/v1/delivery/assigned # Pedidos asignados POST /api/v1/delivery/accept/{id} # Aceptar pedi
Continuar
4 ene
do POST /api/v1/delivery/reject/{id} # Rechazar pedido POST /api/v1/delivery/{id}/pickup # Recoger pedido POST /api/v1/delivery/{id}/deliver # Marcar entrega
Ubicación
POST /api/v1/delivery/location # Actualizar ubicación GPS GET /api/v1/delivery/location/history # Historial de ubicaciones
Reportes
GET /api/v1/delivery/stats # Estadísticas del domiciliario GET /api/v1/delivery/earnings # Ganancias del período

### 6.11 Caja y Pagos
Pagos
POST /api/v1/payments # Registrar pago GET /api/v1/payments/{order_id} # Ver pagos de un pedido PUT /api/v1/payments/{id} # Actualizar pago DELETE /api/v1/payments/{id} # Anular pago
Caja
POST /api/v1/cash/open # Abrir caja POST /api/v1/cash/close # Cierre de caja GET /api/v1/cash/closures # Historial de cierres GET /api/v1/cash/current-shift # Turno actual GET /api/v1/cash/summary # Resumen del día

### 6.12 Reportes
Reportes básicos
GET /api/v1/reports/daily # Reporte diario GET /api/v1/reports/weekly # Reporte semanal GET /api/v1/reports/monthly # Reporte mensual
Reportes específicos
GET /api/v1/reports/sales # Reporte de ventas GET /api/v1/reports/products # Productos más vendidos GET /api/v1/reports/inventory # Reporte de inventario GET /api/v1/reports/delivery-persons # Reporte de domiciliarios GET /api/v1/reports/consolidated # Consolidado (todas sucursales)
Reportes personalizados
POST /api/v1/reports/custom # Reporte personalizado GET /api/v1/reports/export/{format} # Exportar (PDF/Excel/CSV)

### 6.13 Monitoreo y Performance
GET /api/v1/monitoring/health # Health check GET /api/v1/monitoring/performance # Dashboard de performance GET /api/v1/monitoring/queue-status # Estado de la cola POST /api/v1/monitoring/scale-workers # Escalar workers manualmente GET /api/v1/monitoring/alerts # Alertas activas POST /api/v1/monitoring/clear-cache # Limpiar cache GET /api/v1/monitoring/metrics # Métricas del sistema

### 6.14 Configuración
GET /api/v1/settings # Configuración del negocio PUT /api/v1/settings # Actualizar configuración GET /api/v1/settings/printers # Configuración de impresoras PUT /api/v1/settings/printers # Actualizar impresoras GET /api/v1/settings/notifications # Configuración de notificaciones PUT /api/v1/settings/notifications # Actualizar notificaciones

### 6.15 PWA Cliente (Pública)
Menú público
GET /api/v1/client/menu/{slug} # Obtener menú del negocio GET /api/v1/client/categories/{slug} # Categorías públicas GET /api/v1/client/products/{slug} # Productos públicos GET /api/v1/client/product/{id} # Detalle de producto
Pedidos desde PWA Cliente
POST /api/v1/client/orders # Crear pedido público GET /api/v1/client/orders/{id}/track # Rastrear pedido GET /api/v1/client/orders/{id}/status # Estado del pedido
Cliente (opcional)
POST /api/v1/client/register # Registro de cliente POST /api/v1/client/login # Login de cliente GET /api/v1/client/me # Datos del cliente GET /api/v1/client/orders/history # Historial de pedidos

---

## 7. WEBSOCKETS Y TIEMPO REAL

### 7.1 Arquitectura de WebSockets

**Implementación con Socket.IO:**
```python
# backend/app/core/websockets.py
from socketio import AsyncServer
import socketio

# Configuración optimizada
sio = AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    ping_timeout=60,
    ping_interval=25,
    compression_threshold=1024,
    logger=False,
    engineio_logger=False
)

# Middleware de autenticación
@sio.event
async def connect(sid, environ, auth):
    """
    Conexión de cliente con autenticación JWT
    """
    try:
        token = auth.get('token')
        if not token:
            raise ConnectionRefusedError('Missing token')
        
        # Verificar JWT
        user_data = await verify_jwt_token(token)
        
        # Guardar datos del usuario en sesión
        await sio.save_session(sid, {
            'user_id': user_data['user_id'],
            'company_id': user_data['company_id'],
            'branch_id': user_data['branch_id'],
            'role': user_data['role']
        })
        
        # Unir a rooms correspondientes
        await join_user_rooms(sid, user_data)
        
        logger.info(f"User {user_data['user_id']} connected", extra={
            'sid': sid,
            'company_id': user_data['company_id']
        })
        
    except Exception as e:
        logger.error(f"Connection refused: {e}")
        raise ConnectionRefusedError('Invalid authentication')

@sio.event
async def disconnect(sid):
    """
    Desconexión de cliente
    """
    session = await sio.get_session(sid)
    logger.info(f"User {session.get('user_id')} disconnected")

async def join_user_rooms(sid: str, user_data: dict):
    """
    Unir usuario a sus rooms correspondientes
    """
    company_id = user_data['company_id']
    branch_id = user_data['branch_id']
    role = user_data['role']
    
    # Room principal de la empresa
    sio.enter_room(sid, f"company_{company_id}")
    
    # Room de la sucursal
    if branch_id:
        sio.enter_room(sid, f"branch_{company_id}_{branch_id}")
    
    # Rooms específicos por rol
    if role == 'kitchen':
        sio.enter_room(sid, f"kitchen_{company_id}_{branch_id}")
    
    elif role == 'cashier':
        sio.enter_room(sid, f"cashier_{company_id}_{branch_id}")
    
    elif role == 'delivery':
        sio.enter_room(sid, f"delivery_{user_data['user_id']}")
        sio.enter_room(sid, f"delivery_all_{company_id}")
    
    elif role == 'admin':
        sio.enter_room(sid, f"admin_{company_id}")
    
    logger.debug(f"User joined rooms", extra={
        'user_id': user_data['user_id'],
        'role': role
    })
```

### 7.2 Eventos del Sistema

#### Eventos de Pedidos
```python
# backend/app/services/notification_service.py

class NotificationService:
    def __init__(self, socketio):
        self.sio = socketio
    
    async def notify_new_order(self, order: Order):
        """
        Notificar nuevo pedido a cocina
        """
        await self.sio.emit(
            'order:created',
            {
                'order_id': order.id,
                'consecutive': order.consecutive,
                'type': order.order_type,
                'table_number': order.table_number,
                'total': float(order.total),
                'items': [
                    {
                        'product_name': item.product.name,
                        'quantity': item.quantity,
                        'modifiers': [
                            {
                                'name': mod.modifier.name,
                                'quantity': mod.quantity
                            }
                            for mod in item.modifiers
                        ],
                        'notes': item.notes
                    }
                    for item in order.items
                ],
                'timestamp': order.created_at.isoformat()
            },
            room=f"kitchen_{order.company_id}_{order.branch_id}"
        )
    
    async def notify_status_changed(self, order: Order, old_status: str):
        """
        Notificar cambio de estado
        """
        await self.sio.emit(
            'order:status_changed',
            {
                'order_id': order.id,
                'consecutive': order.consecutive,
                'old_status': old_status,
                'new_status': order.status,
                'timestamp': datetime.now().isoformat()
            },
            room=f"branch_{order.company_id}_{order.branch_id}"
        )
        
        # Si el pedido está listo, notificar también a caja
        if order.status == 'ready':
            await self.sio.emit(
                'order:ready',
                {
                    'order_id': order.id,
                    'consecutive': order.consecutive,
                    'type': order.order_type,
                    'table_number': order.table_number
                },
                room=f"cashier_{order.company_id}_{order.branch_id}"
            )
    
    async def notify_order_assigned(self, order: Order):
        """
        Notificar asignación a domiciliario
        """
        await self.sio.emit(
            'delivery:assigned',
            {
                'order_id': order.id,
                'consecutive': order.consecutive,
                'customer_name': order.customer_name,
                'customer_phone': order.customer_phone,
                'delivery_address': order.delivery_address,
                'delivery_notes': order.delivery_notes,
                'total': float(order.total),
                'items': [...],  # Detalles del pedido
                'timestamp': datetime.now().isoformat()
            },
            room=f"delivery_{order.delivery_person_id}"
        )
```

#### Eventos de Impresión
```python
async def notify_print_queued(self, order_id: int, position: int):
    """
    Notificar que pedido está en cola de impresión
    """
    await self.sio.emit(
        'print:queued',
        {
            'order_id': order_id,
            'position': position,
            'estimated_time': position * 5  # 5 segundos por pedido
        },
        room=f"cashier_{company_id}_{branch_id}"
    )

async def notify_print_completed(self, order_id: int):
    """
    Notificar impresión exitosa
    """
    await self.sio.emit(
        'print:completed',
        {
            'order_id': order_id,
            'success': True,
            'timestamp': datetime.now().isoformat()
        },
        room=f"kitchen_{company_id}_{branch_id}"
    )

async def notify_print_fallback(self, order_data: dict):
    """
    Notificar fallo en impresión (usar fallback)
    """
    await self.sio.emit(
        'print:fallback',
        {
            'order_id': order_data['id'],
            'message': '⚠️ IMPRIMIR MANUALMENTE',
            'alert': True,
            'order_data': order_data
        },
        room=f"kitchen_{order_data['company_id']}_{order_data['branch_id']}"
    )
```

#### Eventos de Domiciliarios
```python
async def notify_location_update(
    self, 
    delivery_person_id: int,
    order_id: int,
    latitude: float,
    longitude: float
):
    """
    Actualización de ubicación de domiciliario
    """
    await self.sio.emit(
        'delivery:location_update',
        {
            'delivery_person_id': delivery_person_id,
            'order_id': order_id,
            'latitude': latitude,
            'longitude': longitude,
            'timestamp': datetime.now().isoformat()
        },
        room=f"admin_{company_id}"
    )

async def notify_delivery_completed(self, order: Order):
    """
    Pedido entregado
    """
    await self.sio.emit(
        'delivery:completed',
        {
            'order_id': order.id,
            'consecutive': order.consecutive,
            'delivery_person_id': order.delivery_person_id,
            'timestamp': order.delivered_at.isoformat()
        },
        room=f"branch_{order.company_id}_{order.branch_id}"
    )
```

#### Eventos del Sistema
```python
async def notify_system_alert(
    self,
    company_id: int,
    alert_type: str,
    message: str,
    severity: str = 'medium'
):
    """
    Alerta de sistema
    """
    await self.sio.emit(
        'system:alert',
        {
            'type': alert_type,
            'severity': severity,
            'message': message,
            'action_required': severity == 'high',
            'timestamp': datetime.now().isoformat()
        },
        room=f"admin_{company_id}"
    )

async def notify_low_stock(self, item: InventoryItem):
    """
    Alerta de stock bajo
    """
    await self.sio.emit(
        'inventory:low_stock',
        {
            'item_id': item.id,
            'item_name': item.name,
            'current_stock': float(item.current_stock),
            'min_stock': float(item.min_stock),
            'branch_id': item.branch_id
        },
        room=f"admin_{item.company_id}"
    )
```

### 7.3 Integración en Frontend
```typescript
// frontend/src/services/websocket.ts
import { io, Socket } from 'socket.io-client';

class WebSocketService {
    private socket: Socket | null = null;
    
    connect(token: string) {
        this.socket = io(process.env.VITE_WS_URL, {
            auth: { token },
            transports: ['websocket'],
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionAttempts: 5
        });
        
        this.socket.on('connect', () => {
            console.log('WebSocket connected');
        });
        
        this.socket.on('disconnect', () => {
            console.log('WebSocket disconnected');
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('Connection error:', error);
        });
    }
    
    // Eventos de pedidos
    onOrderCreated(callback: (data: any) => void) {
        this.socket?.on('order:created', callback);
    }
    
    onOrderStatusChanged(callback: (data: any) => void) {
        this.socket?.on('order:status_changed', callback);
    }
    
    onOrderReady(callback: (data: any) => void) {
        this.socket?.on('order:ready', callback);
    }
    
    // Eventos de impresión
    onPrintQueued(callback: (data: any) => void) {
        this.socket?.on('print:queued', callback);
    }
    
    onPrintCompleted(callback: (data: any) => void) {
        this.socket?.on('print:completed', callback);
    }
    
    onPrintFallback(callback: (data: any) => void) {
        this.socket?.on('print:fallback', callback);
    }
    
    // Eventos de domiciliarios
    onDeliveryAssigned(callback: (data: any) => void) {
        this.socket?.on('delivery:assigned', callback);
    }
    
    onLocationUpdate(callback: (data: any) => void) {
        this.socket?.on('delivery:location_update', callback);
    }
    
    // Eventos de sistema
    onSystemAlert(callback: (data: any) => void) {
        this.socket?.on('system:alert', callback);
    }
    
    onLowStock(callback: (data: any) => void) {
        this.socket?.on('inventory:low_stock', callback);
    }
    
    disconnect() {
        this.socket?.disconnect();
    }
}

export const wsService = new WebSocketService();
```

---

## 8. SEGURIDAD MULTI-TENANT

### 8.1 Middleware de Verificación
```python
# backend/app/core/multi_tenant.py
from fastapi import Depends, HTTPException, status
from typing import Optional

async def verify_company_access(
    company_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Verifica que el usuario tenga acceso a la compañía solicitada
    """
    if current_user.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a este negocio"
        )
    return True

async def verify_branch_access(
    branch_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Verifica acceso a sucursal específica
    - Admin: puede ver todas las sucursales de su negocio
    - Otros roles: solo su sucursal asignada
    """
    if current_user.role == "admin":
        # Admin puede ver cualquier sucursal de su negocio
        branch = await db.execute(
            select(Branch).where(
                Branch.id == branch_id,
                Branch.company_id == current_user.company_id
            )
        )
        branch = branch.scalar_one_or_none()
        
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sucursal no encontrada"
            )
        return True
    
    # Otros roles solo su sucursal
    if current_user.branch_id != branch_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a esta sucursal"
        )
    
    return True

async def verify_active_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Verifica que la suscripción del negocio esté activa
    """
    subscription = await db.execute(
        select(Subscription).where(
            Subscription.company_id == current_user.company_id,
            Subscription.status == "active",
            Subscription.current_period_end > datetime.utcnow()
        )
    )
    subscription = subscription.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Suscripción vencida. Por favor renueva tu plan."
        )
    
    return True

async def verify_plan_limits(
    feature: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Verifica límites del plan actual
    """
    company = await db.get(Company, current_user.company_id)
    
    if feature == "users":
        count = await db.scalar(
            select(func.count(User.id)).where(
                User.company_id == current_user.company_id,
                User.is_active == True
            )
        )
        if count >= company.max_users:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Límite de usuarios alcanzado ({company.max_users}). Actualiza tu plan."
            )
    
    elif feature == "branches":
        count = await db.scalar(
            select(func.count(Branch.id)).where(
                Branch.company_id == current_user.company_id,
                Branch.is_active == True
            )
        )
        if count >= company.max_branches:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Límite de sucursales alcanzado ({company.max_branches}). Actualiza tu plan."
            )
    
    elif feature == "products":
        count = await db.scalar(
            select(func.count(Product.id)).where(
                Product.company_id == current_user.company_id,
                Product.is_active == True
            )
        )
        if count >= company.max_products:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Límite de productos alcanzado ({company.max_products}). Actualiza tu plan."
            )
    
    return True
```

### 8.2 Estructura del JWT
```python
# backend/app/core/security.py
from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict) -> str:
    """
    Crear JWT con información multi-tenant
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """
    Crear refresh token de larga duración
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def create_tokens_for_user(user: User) -> dict:
    """
    Generar tokens completos para usuario
    """
    access_token_data = {
        "sub": str(user.id),
        "company_id": user.company_id,
        "branch_id": user.branch_id,
        "role": user.role_id,
        "email": user.email
    }
    
    access_token = create_access_token(access_token_data)
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }
```

### 8.3 Filtros Automáticos en Queries
```python
# backend/app/repositories/base.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import TypeVar, Generic, Optional, List

ModelType = TypeVar("ModelType")

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db
    
    async def get_by_id(
        self,
        id: int,
        company_id: int
    ) -> Optional[ModelType]:
        """
        Obtener por ID con filtro automático de company_id
        """
        result = await self.db.execute(
            select(self.model).where(
                self.model.id == id,
                self.model.company_id == company_id
            )
        )
        return result.scalar_one_or_none()
    
    async def list(
        self,
        company_id: int,
        branch_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[dict] = None
    ) -> List[ModelType]:
        """
        Listar con filtros multi-tenant automáticos
        """
        query = select(self.model).where(
            self.model.company_id == company_id
        )
        
        # Filtro opcional por sucursal
        if branch_id and hasattr(self.model, 'branch_id'):
            query = query.where(self.model.branch_id == branch_id)
        
        # Filtros adicionales
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        
        # Paginación
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def create(
        self,
        obj: ModelType,
        company_id: int,
        user_id: int
    ) -> ModelType:
        """
        Crear con validación automática de company_id
        """
        obj.company_id = company_id
        
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        
        # Auditoría
        await self._create_audit_log(
            action="create",
            entity=self.model.__tablename__,
            entity_id=obj.id,
            company_id=company_id,
            user_id=user_id
        )
        
        return obj
    
    async def update(
        self,
        id: int,
        updates: dict,
        company_id: int,
        user_id: int
    ) -> Optional[ModelType]:
        """
        Actualizar con verificación de company_id
        """
        obj = await self.get_by_id(id, company_id)
        
        if not obj:
            return None
        
        for key, value in updates.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        
        await self.db.commit()
        await self.db.refresh(obj)
        
        # Auditoría
        await self._create_audit_log(
            action="update",
            entity=self.model.__tablename__,
            entity_id=obj.id,
            company_id=company_id,
            user_id=user_id,
            details=updates
        )
        
        return obj
    
    async def delete(
        self,
        id: int,
        company_id: int,
        user_id: int,
        soft: bool = True
    ) -> bool:
        """
        Eliminar (soft delete por defecto)
        """
        obj = await self.get_by_id(id, company_id)
        
        if not obj:
            return False
        
        if soft and hasattr(obj, 'deleted_at'):
            obj.deleted_at = datetime.utcnow()
        else:
            await self.db.delete(obj)
        
        await self.db.commit()
        
        # Auditoría
        await self._create_audit_log(
            action="delete",
            entity=self.model.__tablename__,
            entity_id=id,
            company_id=company_id,
            user_id=user_id
        )
        
        return True
    
    async def _create_audit_log(
        self,
        action: str,
        entity: str,
        entity_id: int,
        company_id: int,
        user_id: int,
        details: Optional[dict] = None
    ):
        """
        Crear log de auditoría
        """
        log = AuditLog(
            company_id=company_id,
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            details=details
        )
        
        self.db.add(log)
        await self.db.commit()
```

---

## 9. PWA CLIENTE Y MODIFICADORES

### 9.1 Experiencia de Usuario (PWA Cliente)

**Acceso:**
- URL: `cliente.fastops.com/{slug}` o `app.fastops.com/{slug}`
- QR code en mesas/publicidad
- Link directo compartible

**Features Clave:**
```typescript
// frontend-client/src/types/menu.ts
interface MenuItem {
    id: number;
    name: string;
    description: string;
    price: number;
    image_url: string;
    category: string;
    allow_modifiers: boolean;
    preparation_time: number;
}

interface Modifier {
    id: number;
    name: string;
    modifier_type: 'addition' | 'exclusion';
    price: number;
    max_quantity: number;
    is_required: boolean;
}

interface CartItem {
    product: MenuItem;
    quantity: number;
    modifiers: Array<{
        modifier: Modifier;
        quantity: number;
    }>;
    notes: string;
    subtotal: number;
}
```

#### Pantalla de Producto (Builder)
```typescript
// frontend-client/src/components/ProductBuilder.tsx
import { useState } from 'react';

export function ProductBuilder({ product }: { product: MenuItem }) {
    const [quantity, setQuantity] = useState(1);
    const [selectedModifiers, setSelectedModifiers] = useState<Map<number, number>>(new Map());
    const [notes, setNotes] = useState('');
    
    const addModifier = (modifierId: number) => {
        const current = selectedModifiers.get(modifierId) || 0;
        const modifier = product.modifiers.find(m => m.id === modifierId);
        
        if (current < modifier.max_quantity) {
            setSelectedModifiers(new Map(selectedModifiers.set(modifierId, current + 1)));
        }
    };
    
    const removeModifier = (modifierId: number) => {
        const current = selectedModifiers.get(modifierId) || 0;
        if (current > 0) {
            setSelectedModifiers(new Map(selectedModifiers.set(modifierId, current - 1)));
        }
    };
    
    const calculateTotal = () => {
        let total = product.price * quantity;
        
        selectedModifiers.forEach((qty, modifierId) => {
Continuar
4 ene
typescript
            const modifier = product.modifiers.find(m => m.id === modifierId);
            if (modifier && modifier.modifier_type === 'addition') {
                total += modifier.price * qty * quantity;
            }
        });
        
        return total;
    };
    
    const addToCart = () => {
        const cartItem: CartItem = {
            product,
            quantity,
            modifiers: Array.from(selectedModifiers.entries())
                .filter(([_, qty]) => qty > 0)
                .map(([modifierId, qty]) => ({
                    modifier: product.modifiers.find(m => m.id === modifierId)!,
                    quantity: qty
                })),
            notes,
            subtotal: calculateTotal()
        };
        
        dispatch(addToCartAction(cartItem));
        toast.success('Producto agregado al carrito');
    };
    
    return (
        <div className="product-builder">
            {/* Imagen del producto */}
            <img src={product.image_url} alt={product.name} />
            
            <h2>{product.name}</h2>
            <p>{product.description}</p>
            <p className="price">${product.price.toLocaleString()}</p>
            
            {/* Modificadores - Adiciones */}
            <div className="modifiers-section">
                <h3>Adicionales</h3>
                {product.modifiers
                    .filter(m => m.modifier_type === 'addition')
                    .map(modifier => (
                        <div key={modifier.id} className="modifier-item">
                            <div>
                                <span>{modifier.name}</span>
                                <span className="modifier-price">
                                    +${modifier.price.toLocaleString()}
                                </span>
                            </div>
                            
                            <div className="quantity-controls">
                                <button onClick={() => removeModifier(modifier.id)}>
                                    -
                                </button>
                                <span>{selectedModifiers.get(modifier.id) || 0}</span>
                                <button onClick={() => addModifier(modifier.id)}>
                                    +
                                </button>
                            </div>
                        </div>
                    ))}
            </div>
            
            {/* Modificadores - Exclusiones */}
            <div className="modifiers-section">
                <h3>Personalizar</h3>
                {product.modifiers
                    .filter(m => m.modifier_type === 'exclusion')
                    .map(modifier => (
                        <label key={modifier.id} className="exclusion-item">
                            <input
                                type="checkbox"
                                checked={selectedModifiers.has(modifier.id)}
                                onChange={(e) => {
                                    if (e.target.checked) {
                                        addModifier(modifier.id);
                                    } else {
                                        setSelectedModifiers(prev => {
                                            const next = new Map(prev);
                                            next.delete(modifier.id);
                                            return next;
                                        });
                                    }
                                }}
                            />
                            <span>{modifier.name}</span>
                        </label>
                    ))}
            </div>
            
            {/* Notas especiales */}
            <div className="notes-section">
                <label>Notas de cocina (opcional)</label>
                <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Ej: Sin sal, bien cocido..."
                    maxLength={200}
                />
            </div>
            
            {/* Cantidad del producto */}
            <div className="quantity-section">
                <label>Cantidad</label>
                <div className="quantity-controls large">
                    <button onClick={() => setQuantity(Math.max(1, quantity - 1))}>
                        -
                    </button>
                    <span>{quantity}</span>
                    <button onClick={() => setQuantity(quantity + 1)}>
                        +
                    </button>
                </div>
            </div>
            
            {/* Botón agregar al carrito */}
            <button 
                className="btn-add-to-cart"
                onClick={addToCart}
            >
                Agregar ${calculateTotal().toLocaleString()}
            </button>
        </div>
    );
}
Carrito Inteligente
typescript
// frontend-client/src/components/Cart.tsx
export function Cart() {
    const cart = useSelector((state: RootState) => state.cart.items);
    const company = useSelector((state: RootState) => state.app.company);
    
    const groupedItems = useMemo(() => {
        // Agrupar ítems idénticos (mismo producto + mismos modificadores)
        return cart.reduce((groups, item) => {
            const key = generateItemKey(item);
            const existing = groups.find(g => g.key === key);
            
            if (existing) {
                existing.quantity += item.quantity;
                existing.subtotal += item.subtotal;
            } else {
                groups.push({
                    key,
                    ...item
                });
            }
            
            return groups;
        }, [] as CartItem[]);
    }, [cart]);
    
    const total = useMemo(() => {
        return groupedItems.reduce((sum, item) => sum + item.subtotal, 0);
    }, [groupedItems]);
    
    return (
        <div className="cart">
            <h2>Tu pedido</h2>
            
            {groupedItems.map((item, index) => (
                <div key={index} className="cart-item">
                    <div className="item-header">
                        <span className="quantity">{item.quantity}x</span>
                        <span className="name">{item.product.name}</span>
                        <span className="price">
                            ${item.subtotal.toLocaleString()}
                        </span>
                    </div>
                    
                    {/* Mostrar modificadores */}
                    {item.modifiers.length > 0 && (
                        <div className="item-modifiers">
                            {item.modifiers.map((mod, idx) => (
                                <div key={idx} className="modifier">
                                    <span>
                                        {mod.quantity > 1 ? `${mod.quantity}x ` : ''}
                                        {mod.modifier.name}
                                    </span>
                                    {mod.modifier.price > 0 && (
                                        <span className="modifier-price">
                                            +${(mod.modifier.price * mod.quantity).toLocaleString()}
                                        </span>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                    
                    {/* Notas */}
                    {item.notes && (
                        <div className="item-notes">
                            <i>"{item.notes}"</i>
                        </div>
                    )}
                    
                    {/* Acciones */}
                    <div className="item-actions">
                        <button onClick={() => dispatch(editCartItem(index))}>
                            Editar
                        </button>
                        <button onClick={() => dispatch(removeCartItem(index))}>
                            Eliminar
                        </button>
                    </div>
                </div>
            ))}
            
            {/* Total */}
            <div className="cart-total">
                <span>Total</span>
                <span className="total-amount">
                    ${total.toLocaleString()}
                </span>
            </div>
            
            {/* Botón checkout */}
            <button 
                className="btn-checkout"
                onClick={() => navigate('/checkout')}
                disabled={cart.length === 0}
            >
                Continuar
            </button>
        </div>
    );
}

function generateItemKey(item: CartItem): string {
    // Generar key único basado en producto + modificadores
    const modifiersKey = item.modifiers
        .map(m => `${m.modifier.id}:${m.quantity}`)
        .sort()
        .join('|');
    
    return `${item.product.id}:${modifiersKey}:${item.notes}`;
}
9.2 Checkout y Tipos de Pedido
typescript
// frontend-client/src/pages/Checkout.tsx
export function Checkout() {
    const [orderType, setOrderType] = useState<'mesa' | 'llevar' | 'domicilio'>('mesa');
    const [customerData, setCustomerData] = useState({
        name: '',
        phone: '',
        email: '',
        tableNumber: '',
        deliveryAddress: '',
        deliveryNotes: ''
    });
    
    const handleSubmit = async () => {
        const orderData = {
            order_type: orderType,
            items: cart.map(item => ({
                product_id: item.product.id,
                quantity: item.quantity,
                modifiers: item.modifiers.map(mod => ({
                    modifier_id: mod.modifier.id,
                    quantity: mod.quantity
                })),
                notes: item.notes
            })),
            customer_name: customerData.name,
            customer_phone: customerData.phone,
            customer_email: customerData.email,
            table_number: orderType === 'mesa' ? customerData.tableNumber : null,
            delivery_address: orderType === 'domicilio' ? customerData.deliveryAddress : null,
            delivery_notes: orderType === 'domicilio' ? customerData.deliveryNotes : null
        };
        
        try {
            const response = await api.post('/client/orders', orderData);
            
            // Limpiar carrito
            dispatch(clearCart());
            
            // Redirigir a tracking
            navigate(`/track/${response.data.id}`);
            
        } catch (error) {
            toast.error('Error al crear el pedido');
        }
    };
    
    return (
        <div className="checkout">
            <h2>Finalizar pedido</h2>
            
            {/* Selector de tipo de pedido */}
            <div className="order-type-selector">
                <button 
                    className={orderType === 'mesa' ? 'active' : ''}
                    onClick={() => setOrderType('mesa')}
                >
                    🪑 Mesa
                </button>
                <button 
                    className={orderType === 'llevar' ? 'active' : ''}
                    onClick={() => setOrderType('llevar')}
                >
                    🎒 Para Llevar
                </button>
                <button 
                    className={orderType === 'domicilio' ? 'active' : ''}
                    onClick={() => setOrderType('domicilio')}
                >
                    🏍️ Domicilio
                </button>
            </div>
            
            {/* Formulario según tipo de pedido */}
            {orderType === 'mesa' && (
                <div className="form-section">
                    <label>Número de mesa</label>
                    <input
                        type="text"
                        value={customerData.tableNumber}
                        onChange={(e) => setCustomerData({
                            ...customerData,
                            tableNumber: e.target.value
                        })}
                        placeholder="Ej: 5"
                        required
                    />
                </div>
            )}
            
            {orderType === 'domicilio' && (
                <>
                    <div className="form-section">
                        <label>Dirección de entrega *</label>
                        <input
                            type="text"
                            value={customerData.deliveryAddress}
                            onChange={(e) => setCustomerData({
                                ...customerData,
                                deliveryAddress: e.target.value
                            })}
                            placeholder="Calle 123 #45-67"
                            required
                        />
                    </div>
                    
                    <div className="form-section">
                        <label>Notas de entrega (opcional)</label>
                        <textarea
                            value={customerData.deliveryNotes}
                            onChange={(e) => setCustomerData({
                                ...customerData,
                                deliveryNotes: e.target.value
                            })}
                            placeholder="Ej: Casa amarilla, timbre no funciona"
                        />
                    </div>
                </>
            )}
            
            {/* Datos del cliente (siempre) */}
            <div className="form-section">
                <label>Nombre *</label>
                <input
                    type="text"
                    value={customerData.name}
                    onChange={(e) => setCustomerData({
                        ...customerData,
                        name: e.target.value
                    })}
                    placeholder="Tu nombre"
                    required
                />
            </div>
            
            <div className="form-section">
                <label>Teléfono *</label>
                <input
                    type="tel"
                    value={customerData.phone}
                    onChange={(e) => setCustomerData({
                        ...customerData,
                        phone: e.target.value
                    })}
                    placeholder="300 123 4567"
                    required
                />
            </div>
            
            <div className="form-section">
                <label>Email (opcional)</label>
                <input
                    type="email"
                    value={customerData.email}
                    onChange={(e) => setCustomerData({
                        ...customerData,
                        email: e.target.value
                    })}
                    placeholder="tu@email.com"
                />
            </div>
            
            {/* Resumen del pedido */}
            <div className="order-summary">
                <h3>Resumen</h3>
                {/* ... items del carrito ... */}
                <div className="total">
                    <span>Total a pagar</span>
                    <span>${total.toLocaleString()}</span>
                </div>
            </div>
            
            {/* Botón confirmar */}
            <button 
                className="btn-confirm"
                onClick={handleSubmit}
            >
                Confirmar pedido
            </button>
        </div>
    );
}
9.3 Tracking en Tiempo Real
typescript
// frontend-client/src/pages/OrderTracking.tsx
export function OrderTracking() {
    const { orderId } = useParams();
    const [order, setOrder] = useState<Order | null>(null);
    const wsService = useWebSocket();
    
    useEffect(() => {
        // Cargar datos iniciales
        loadOrder();
        
        // Conectar a WebSocket para actualizaciones
        wsService.connect();
        
        // Suscribirse a eventos del pedido
        wsService.onOrderStatusChanged((data) => {
            if (data.order_id === parseInt(orderId)) {
                setOrder(prev => ({
                    ...prev!,
                    status: data.new_status
                }));
            }
        });
        
        // Suscribirse a ubicación del domiciliario
        wsService.onLocationUpdate((data) => {
            if (data.order_id === parseInt(orderId)) {
                // Actualizar mapa con ubicación
                updateDeliveryLocation(data.latitude, data.longitude);
            }
        });
        
        return () => {
            wsService.disconnect();
        };
    }, [orderId]);
    
    const loadOrder = async () => {
        try {
            const response = await api.get(`/client/orders/${orderId}/track`);
            setOrder(response.data);
        } catch (error) {
            toast.error('Pedido no encontrado');
        }
    };
    
    const getStatusInfo = (status: string) => {
        const statuses = {
            'pending': {
                icon: '⏳',
                title: 'Pedido recibido',
                description: 'Tu pedido ha sido recibido y está en cola'
            },
            'confirmed': {
                icon: '✅',
                title: 'Pedido confirmado',
                description: 'Hemos confirmado tu pedido'
            },
            'preparing': {
                icon: '👨‍🍳',
                title: 'En preparación',
                description: 'Estamos preparando tu pedido con cuidado'
            },
            'ready': {
                icon: '🎉',
                title: '¡Listo!',
                description: order?.order_type === 'domicilio' 
                    ? 'Tu pedido está listo y saldrá pronto'
                    : 'Tu pedido está listo para recoger'
            },
            'in_delivery': {
                icon: '🏍️',
                title: 'En camino',
                description: 'Tu pedido va en camino'
            },
            'delivered': {
                icon: '✨',
                title: 'Entregado',
                description: '¡Disfruta tu pedido!'
            }
        };
        
        return statuses[status] || statuses['pending'];
    };
    
    if (!order) {
        return <div>Cargando...</div>;
    }
    
    const statusInfo = getStatusInfo(order.status);
    
    return (
        <div className="order-tracking">
            {/* Header */}
            <div className="tracking-header">
                <h2>Pedido #{order.consecutive}</h2>
                <p className="order-type">
                    {order.order_type === 'mesa' && '🪑 Mesa'}
                    {order.order_type === 'llevar' && '🎒 Para Llevar'}
                    {order.order_type === 'domicilio' && '🏍️ Domicilio'}
                </p>
            </div>
            
            {/* Estado actual */}
            <div className="current-status">
                <div className="status-icon">{statusInfo.icon}</div>
                <h3>{statusInfo.title}</h3>
                <p>{statusInfo.description}</p>
            </div>
            
            {/* Timeline */}
            <div className="status-timeline">
                <div className={`timeline-step ${order.status !== 'pending' ? 'completed' : 'active'}`}>
                    <div className="step-marker"></div>
                    <div className="step-content">
                        <p className="step-title">Pedido recibido</p>
                        <p className="step-time">
                            {formatTime(order.created_at)}
                        </p>
                    </div>
                </div>
                
                <div className={`timeline-step ${['preparing', 'ready', 'delivered'].includes(order.status) ? 'completed' : order.status === 'confirmed' ? 'active' : ''}`}>
                    <div className="step-marker"></div>
                    <div className="step-content">
                        <p className="step-title">En preparación</p>
                        {order.started_at && (
                            <p className="step-time">
                                {formatTime(order.started_at)}
                            </p>
                        )}
                    </div>
                </div>
                
                <div className={`timeline-step ${['ready', 'in_delivery', 'delivered'].includes(order.status) ? 'completed' : order.status === 'preparing' ? 'active' : ''}`}>
                    <div className="step-marker"></div>
                    <div className="step-content">
                        <p className="step-title">Listo</p>
                        {order.ready_at && (
                            <p className="step-time">
                                {formatTime(order.ready_at)}
                            </p>
                        )}
                    </div>
                </div>
                
                {order.order_type === 'domicilio' && (
                    <>
                        <div className={`timeline-step ${order.status === 'delivered' ? 'completed' : order.status === 'in_delivery' ? 'active' : ''}`}>
                            <div className="step-marker"></div>
                            <div className="step-content">
                                <p className="step-title">En camino</p>
                            </div>
                        </div>
                        
                        <div className={`timeline-step ${order.status === 'delivered' ? 'completed' : ''}`}>
                            <div className="step-marker"></div>
                            <div className="step-content">
                                <p className="step-title">Entregado</p>
                                {order.delivered_at && (
                                    <p className="step-time">
                                        {formatTime(order.delivered_at)}
                                    </p>
                                )}
                            </div>
                        </div>
                    </>
                )}
            </div>
            
            {/* Mapa (solo para domicilios) */}
            {order.order_type === 'domicilio' && order.status === 'in_delivery' && (
                <div className="delivery-map">
                    <h3>Ubicación del domiciliario</h3>
                    {/* Mapa con marcador actualizado en tiempo real */}
                    <DeliveryMap orderId={order.id} />
                </div>
            )}
            
            {/* Detalles del pedido */}
            <div className="order-details">
                <h3>Detalles del pedido</h3>
                {order.items.map((item, index) => (
                    <div key={index} className="order-item">
                        <span className="quantity">{item.quantity}x</span>
                        <div className="item-info">
                            <p className="item-name">{item.product_name}</p>
                            {item.modifiers.length > 0 && (
                                <ul className="item-modifiers">
                                    {item.modifiers.map((mod, idx) => (
                                        <li key={idx}>
                                            {mod.quantity > 1 ? `${mod.quantity}x ` : ''}
                                            {mod.name}
                                        </li>
                                    ))}
                                </ul>
                            )}
                            {item.notes && (
                                <p className="item-notes">
                                    <i>"{item.notes}"</i>
                                </p>
                            )}
                        </div>
                    </div>
                ))}
                
                <div className="order-total">
                    <span>Total</span>
                    <span>${order.total.toLocaleString()}</span>
                </div>
            </div>
            
            {/* Información de contacto */}
            {order.order_type === 'domicilio' && order.delivery_person && (
                <div className="contact-info">
                    <h3>Tu domiciliario</h3>
                    <p>{order.delivery_person.name}</p>
                    <a href={`tel:${order.delivery_person.phone}`} className="btn-call">
                        📞 Llamar
                    </a>
                </div>
            )}
        </div>
    );
}
9.4 Endpoints API PWA Cliente
python
# backend/app/routers/client.py
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

router = APIRouter(prefix="/client", tags=["Cliente PWA"])

@router.get("/menu/{slug}")
async def get_public_menu(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener menú público del negocio
    """
    # Buscar compañía por slug
    company = await db.execute(
        select(Company).where(
            Company.slug == slug,
            Company.is_active == True
        )
    )
    company = company.scalar_one_or_none()
    
    if not company:
        raise HTTPException(404, "Negocio no encontrado")
    
    # Obtener categorías y productos
    categories = await db.execute(
        select(Category).where(
            Category.company_id == company.id,
            Category.is_active == True
        ).order_by(Category.sort_order)
    )
    categories = categories.scalars().all()
    
    products = await db.execute(
        select(Product).where(
            Product.company_id == company.id,
            Product.is_active == True
        )
    )
    products = products.scalars().all()
    
    # Obtener modificadores
    product_ids = [p.id for p in products]
    modifiers = await db.execute(
        select(ProductModifier).where(
            ProductModifier.product_id.in_(product_ids),
            ProductModifier.is_available == True
        )
    )
    modifiers = modifiers.scalars().all()
    
    # Agrupar modificadores por producto
    modifiers_by_product = {}
    for mod in modifiers:
        if mod.product_id not in modifiers_by_product:
            modifiers_by_product[mod.product_id] = []
        modifiers_by_product[mod.product_id].append(mod)
    
    return {
        "company": {
            "name": company.name,
            "logo_url": company.logo_url,
            "primary_color": company.primary_color
        },
        "categories": [
            {
                "id": cat.id,
                "name": cat.name,
                "icon": cat.icon,
                "products": [
                    {
                        **p.dict(),
                        "modifiers": modifiers_by_product.get(p.id, [])
                    }
                    for p in products if p.category_id == cat.id
                ]
            }
            for cat in categories
        ]
    }

@router.post("/orders")
async def create_public_order(
    order: ClientOrderCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Crear pedido desde PWA Cliente
    """
    # Validar que la compañía existe
    company = await db.get(Company, order.company_id)
    if not company or not company.is_active:
        raise HTTPException(404, "Negocio no disponible")
    
    # Validar productos y calcular total
    total = Decimal('0')
    items_data = []
    
    for item in order.items:
        product = await db.get(Product, item.product_id)
        if not product or product.company_id != company.id:
            raise HTTPException(400, f"Producto {item.product_id} no válido")
        
        item_total = product.price * item.quantity
        
        # Procesar modificadores
        for modifier in item.modifiers:
            mod = await db.get(ProductModifier, modifier.modifier_id)
            if not mod or mod.product_id != product.id:
                raise HTTPException(400, f"Modificador {modifier.modifier_id} no válido")
            
            if mod.modifier_type == 'addition':
                item_total += mod.price * modifier.quantity * item.quantity
        
        total += item_total
        items_data.append({
            'product': product,
            'item': item,
            'subtotal': item_total
        })
    
    # Generar consecutivo
    consecutive = await generate_consecutive(
        company_id=company.id,
        branch_id=company.main_branch_id,  # Sucursal principal
        order_type=order.order_type,
        db=db
    )
    
    # Crear pedido
    new_order = Order(
        company_id=company.id,
        branch_id=company.main_branch_id,
        consecutive=consecutive,
        order_type=order.order_type,
        table_number=order.table_number,
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        customer_email=order.customer_email,
        delivery_address=order.delivery_address,
        delivery_notes=order.delivery_notes,
        status='pending',
        subtotal=total,
        total=total,
        created_by=None  # Pedido público
    )
    
    db.add(new_order)
    await db.flush()
    
    # Crear items del pedido
    for item_data in items_data:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item_data['item'].product_id,
            quantity=item_data['item'].quantity,
            unit_price=item_data['product'].price,
            subtotal=item_data['subtotal'],
            notes=item_data['item'].notes
        )
        
        db.add(order_item)
        await db.flush()
        
        # Crear modificadores del item
        for modifier in item_data['item'].modifiers:
            mod = await db.get(ProductModifier, modifier.modifier_id)
            
            order_item_modifier = OrderItemModifier(
                order_item_id=order_item.id,
                modifier_id=modifier.modifier_id,
                quantity=modifier.quantity,
                unit_price=mod.price,
                subtotal=mod.price * modifier.quantity * item_data['item'].quantity
            )
            
            db.add(order_item_modifier)
    
    await db.commit()
    await db.refresh(new_order)
    
    # Encolar impresión
    print_order_task.delay(
        order_id=new_order.id,
        company_id=company.id,
        branch_id=new_order.branch_id
    )
    
    # Notificar WebSocket
    await notify_new_order(new_order)
    
    return {
        "id": new_order.id,
        "consecutive": new_order.consecutive,
        "status": new_order.status,
        "total": float(new_order.total),
        "tracking_url": f"/track/{new_order.id}"
    }

@router.get("/orders/{order_id}/track")
async def track_order(
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Rastrear estado del pedido
    """
    order = await db.get(Order, order_id)
    
    if not order:
        raise HTTPException(404, "Pedido no encontrado")
    
    # Cargar relaciones
    await db.refresh(order, ["items", "delivery_person"])
    
    return {
        "id": order.id,
        "consecutive": order.consecutive,
        "order_type": order.order_type,
        "status": order.status,
        "total": float(order.total),
        "created_at": order.created_at,
        "started_at": order.started_at,
        "ready_at": order.ready_at,
        "delivered_at": order.delivered_at,
        "items": [
            {
                "product_name": item.product.name,
                "quantity": item.quantity,
                "modifiers": [
                    {
                        "name": mod.modifier.name,
                        "quantity": mod.quantity
                    }
                    for mod in item.modifiers
                ],
                "notes": item.notes
            }
            for item in order.items
        ],
        "delivery_person": {
            "name": order.delivery_person.full_name,
            "phone": order.delivery_person.phone
        } if order.delivery_person else None
    }
________________________________________
10. SISTEMA RBAC AVANZADO
10.1 Arquitectura RBAC
Sistema completado exitosamente en Diciembre 2025
**
Continuar
10:45 a.m.
Componentes principales:**
1.	Roles jerárquicos con niveles de autoridad
2.	Permisos granulares (resource.action)
3.	Categorías de permisos para organización
4.	Cache Redis para optimización
5.	Decoradores para protección de rutas
10.2 Servicios RBAC
python
# backend/app/services/rbac_service.py
from typing import List, Optional
import json

class RBACService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis
        self.cache_ttl = 3600  # 1 hora
    
    async def get_user_permissions(
        self, 
        user_id: int,
        use_cache: bool = True
    ) -> List[str]:
        """
        Obtener permisos de usuario (con cache)
        """
        cache_key = f"user:permissions:{user_id}"
        
        # Intentar obtener de cache
        if use_cache:
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)
        
        # Obtener de DB
        user = await self.db.get(User, user_id)
        if not user or not user.role_id:
            return []
        
        role = await self.db.get(Role, user.role_id)
        if not role:
            return []
        
        # Obtener permisos del rol
        role_permissions = await self.db.execute(
            select(Permission)
            .join(RolePermission)
            .where(RolePermission.role_id == role.id)
            .where(Permission.is_active == True)
        )
        
        permissions = [
            f"{p.resource}.{p.action}"
            for p in role_permissions.scalars().all()
        ]
        
        # Guardar en cache
        await self.redis.setex(
            cache_key,
            self.cache_ttl,
            json.dumps(permissions)
        )
        
        return permissions
    
    async def has_permission(
        self,
        user_id: int,
        permission: str
    ) -> bool:
        """
        Verificar si usuario tiene permiso específico
        """
        permissions = await self.get_user_permissions(user_id)
        return permission in permissions
    
    async def invalidate_user_cache(self, user_id: int):
        """
        Invalidar cache de permisos de usuario
        """
        await self.redis.delete(f"user:permissions:{user_id}")
    
    async def assign_permission_to_role(
        self,
        role_id: int,
        permission_id: int,
        granted_by: int
    ):
        """
        Asignar permiso a rol
        """
        role_permission = RolePermission(
            role_id=role_id,
            permission_id=permission_id,
            granted_by=granted_by
        )
        
        self.db.add(role_permission)
        await self.db.commit()
        
        # Invalidar cache de todos los usuarios con este rol
        users = await self.db.execute(
            select(User.id).where(User.role_id == role_id)
        )
        
        for (user_id,) in users:
            await self.invalidate_user_cache(user_id)
    
    async def revoke_permission_from_role(
        self,
        role_id: int,
        permission_id: int
    ):
        """
        Revocar permiso de rol
        """
        await self.db.execute(
            delete(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id
            )
        )
        
        await self.db.commit()
        
        # Invalidar cache
        users = await self.db.execute(
            select(User.id).where(User.role_id == role_id)
        )
        
        for (user_id,) in users:
            await self.invalidate_user_cache(user_id)
10.3 Decoradores de Seguridad
python
# backend/app/core/security_decorators.py
from functools import wraps
from fastapi import HTTPException, status

def require_permission(permission: str):
    """
    Decorador para requerir permiso específico
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Obtener current_user de kwargs
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Autenticación requerida"
                )
            
            # Verificar permiso
            rbac_service = get_rbac_service()
            has_perm = await rbac_service.has_permission(
                current_user.id,
                permission
            )
            
            if not has_perm:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permiso requerido: {permission}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def require_role(role_name: str):
    """
    Decorador para requerir rol específico
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Autenticación requerida"
                )
            
            if current_user.role.name != role_name:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Rol requerido: {role_name}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def require_any_permission(*permissions: str):
    """
    Decorador para requerir AL MENOS UNO de los permisos
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Autenticación requerida"
                )
            
            rbac_service = get_rbac_service()
            user_perms = await rbac_service.get_user_permissions(current_user.id)
            
            has_any = any(perm in user_perms for perm in permissions)
            
            if not has_any:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Se requiere uno de: {', '.join(permissions)}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
10.4 Uso en Endpoints
python
# backend/app/routers/products.py
@router.post("/products", response_model=ProductResponse)
@require_permission("products.create")
async def create_product(
    product: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Crear producto (requiere permiso products.create)
    """
    # ...implementación...

@router.delete("/products/{id}")
@require_permission("products.delete")
async def delete_product(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Eliminar producto (requiere permiso products.delete)
    """
    # ...implementación...

@router.get("/admin/reports")
@require_any_permission("reports.view", "reports.admin")
async def get_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Ver reportes (requiere reports.view O reports.admin)
    """
    # ...implementación...
10.5 Permisos Predefinidos
python
# backend/app/seeds/permissions.py
DEFAULT_PERMISSIONS = [
    # Productos
    {"resource": "products", "action": "view", "category": "Productos"},
    {"resource": "products", "action": "create", "category": "Productos"},
    {"resource": "products", "action": "update", "category": "Productos"},
    {"resource": "products", "action": "delete", "category": "Productos"},
    
    # Pedidos
    {"resource": "orders", "action": "view", "category": "Pedidos"},
    {"resource": "orders", "action": "create", "category": "Pedidos"},
    {"resource": "orders", "action": "update", "category": "Pedidos"},
    {"resource": "orders", "action": "cancel", "category": "Pedidos"},
    {"resource": "orders", "action": "assign", "category": "Pedidos"},
    
    # Inventario
    {"resource": "inventory", "action": "view", "category": "Inventario"},
    {"resource": "inventory", "action": "create", "category": "Inventario"},
    {"resource": "inventory", "action": "update", "category": "Inventario"},
    {"resource": "inventory", "action": "adjust", "category": "Inventario"},
    
    # Reportes
    {"resource": "reports", "action": "view", "category": "Reportes"},
    {"resource": "reports", "action": "export", "category": "Reportes"},
    {"resource": "reports", "action": "admin", "category": "Reportes"},
    
    # Usuarios
    {"resource": "users", "action": "view", "category": "Usuarios"},
    {"resource": "users", "action": "create", "category": "Usuarios"},
    {"resource": "users", "action": "update", "category": "Usuarios"},
    {"resource": "users", "action": "delete", "category": "Usuarios"},
    
    # Roles
    {"resource": "roles", "action": "view", "category": "RBAC"},
    {"resource": "roles", "action": "create", "category": "RBAC"},
    {"resource": "roles", "action": "update", "category": "RBAC"},
    {"resource": "roles", "action": "delete", "category": "RBAC"},
    {"resource": "roles", "action": "assign_permissions", "category": "RBAC"},
    
    # Configuración
    {"resource": "settings", "action": "view", "category": "Configuración"},
    {"resource": "settings", "action": "update", "category": "Configuración"},
    
    # Caja
    {"resource": "cash", "action": "open", "category": "Caja"},
    {"resource": "cash", "action": "close", "category": "Caja"},
    {"resource": "cash", "action": "view_closures", "category": "Caja"},
]

DEFAULT_ROLES = {
    "admin": {
        "level": 100,
        "permissions": [
            # Todos los permisos
            "products.*",
            "orders.*",
            "inventory.*",
            "reports.*",
            "users.*",
            "roles.*",
            "settings.*",
            "cash.*"
        ]
    },
    "cashier": {
        "level": 50,
        "permissions": [
            "products.view",
            "orders.view",
            "orders.create",
            "orders.update",
            "orders.assign",
            "cash.open",
            "cash.close",
            "reports.view"
        ]
    },
    "kitchen": {
        "level": 30,
        "permissions": [
            "orders.view",
            "orders.update",
            "inventory.view"
        ]
    },
    "delivery": {
        "level": 20,
        "permissions": [
            "orders.view",
            "orders.update"
        ]
    }
}
```

---

## 11. PLAN DE DESARROLLO POR FASES

### FASE 0.5: PREPARACIÓN MULTI-TENANT ⏱️ 2 días | 🔴 CRÍTICA

**Objetivo:** Establecer base de datos multi-tenant antes de cualquier desarrollo

**Tareas:**
1. ✅ Crear modelos SQLModel multi-tenant
   - `Company`, `Branch`, `Subscription`, `OrderCounter`
   
2. ✅ Actualizar modelos existentes
   - Agregar `company_id` a TODAS las tablas
   - Agregar `branch_id` donde aplique
   
3. ✅ Script de migraciones SQL completo
   - Crear tablas nuevas
   - Alterar tablas existentes
   - Crear índices optimizados
   
4. ✅ Seed data multi-tenant
   - 2 companies de prueba
   - 2-3 branches por company
   - Usuarios de prueba por negocio
   
5. ✅ Validar aislamiento
   - Tests de queries
   - Verificar filtros automáticos

**Entregables:**
- ✅ Modelos SQLModel completos
- ✅ `migrations/001_multi_tenant.sql`
- ✅ `seeds/dev_data.py`
- ✅ README actualizado

---

### FASE 1: BACKEND CORE ⏱️ 1.5 semanas | 🔴 ALTA

**Objetivo:** API funcional con multi-tenancy, RBAC y pedidos básicos

**Tickets:**
1. **AUTH-MT**: Sistema de autenticación multi-tenant
   - JWT con `company_id` y `branch_id`
   - Login, registro, refresh token
   - Middleware de verificación

2. **RBAC-SYSTEM**: Sistema RBAC completo
   - Modelos de roles y permisos
   - Servicio con cache Redis
   - Decoradores de seguridad
   - Seed de permisos predefinidos

3. **COMPANY-CRUD**: Gestión de negocios
   - Endpoints super-admin
   - CRUD completo
   - Gestión de suscripciones

4. **BRANCH-CRUD**: Gestión de sucursales
   - CRUD por compañía
   - Validación de límites

5. **PRODUCTS-CRUD**: Productos y recetas
   - CRUD con filtros multi-tenant
   - Sistema de modificadores
   - Upload de imágenes

6. **ORDERS-ASYNC**: Sistema de pedidos asíncrono
   - Creación con consecutivos por sucursal
   - Cálculo de totales en backend
   - Descuento automático de inventario
   - Estados y transiciones

7. **PRINT-QUEUE**: Cola de impresión
   - Celery + Redis
   - Circuit breaker
   - Sistema de fallback

8. **WEBSOCKETS-MT**: WebSockets aislados
   - Rooms por company y branch
   - Eventos del sistema
   - Notificaciones en tiempo real

**Entregables:**
- API funcional con Postman collection
- Tests unitarios (coverage > 70%)
- Documentación de endpoints

---

### FASE 2: INVENTARIO Y CAJA ⏱️ 1 semana | 🔴 ALTA

**Objetivo:** Control de inventario y cierre de caja

**Tickets:**
1. **INVENTORY-BASIC**: CRUD de inventario
   - Insumos por sucursal
   - Movimientos y entradas
   - Alertas de stock bajo

2. **RECIPES-SYSTEM**: Sistema de recetas
   - Relación producto-insumo
   - Cálculo de costos
   - Descuento automático

3. **PAYMENTS**: Registro de pagos
   - Múltiples métodos
   - Validación de montos

4. **CASH-CLOSURE**: Cierre de caja
   - Cálculo esperado vs real
   - Diferencias y auditoría
   - Reportes de caja

**Entregables:**
- Sistema de inventario funcional
- Cierre de caja automático
- Reportes básicos

---

### FASE 3: DOMICILIARIOS ⏱️ 1 semana | 🟡 MEDIA

**Objetivo:** Control de domiciliarios y entregas

**Tickets:**
1. **DELIVERY-CRUD**: Gestión de domiciliarios
   - CRUD básico
   - Estados (disponible/ocupado)

2. **DELIVERY-GPS**: Sistema GPS
   - Actualización de ubicación
   - Historial de ubicaciones
   - Tracking en tiempo real

3. **DELIVERY-ASSIGNMENT**: Asignación inteligente
   - Manual desde caja
   - Automática (opcional)
   - Notificaciones push

4. **DELIVERY-APP**: PWA para domiciliarios
   - Vista de pedidos asignados
   - Actualización de estados
   - Mapa con ubicación

**Entregables:**
- API de domiciliarios
- PWA domiciliarios funcional
- Sistema de tracking GPS

---

### FASE 4: FRONTEND PWA ADMIN ⏱️ 2 semanas | 🔴 ALTA

**Objetivo:** Interfaz administrativa completa

**Tickets:**
1. **FE-SETUP**: Estructura del proyecto
   - React + TypeScript + Vite
   - Redux Toolkit + RTK Query
   - TailwindCSS + shadcn/ui

2. **FE-AUTH**: Autenticación
   - Login multi-tenant
   - Gestión de tokens
   - Rutas protegidas

3. **FE-DASHBOARD**: Dashboard principal
   - Métricas en tiempo real
   - Gráficas de ventas
   - Alertas del sistema

4. **FE-PRODUCTS**: Gestión de productos
   - CRUD completo
   - Upload de imágenes
   - Gestión de modificadores

5. **FE-ORDERS**: Creación de pedidos
   - Selector de productos
   - Carrito inteligente
   - Tipos de pedido

6. **FE-KITCHEN**: Vista de cocina
   - Pedidos por preparar
   - Actualización de estados
   - Tiempo real con WebSockets

7. **FE-INVENTORY**: Gestión de inventario
   - CRUD de insumos
   - Movimientos
   - Alertas

8. **FE-REPORTS**: Reportes
   - Ventas del día
   - Productos top
   - Inventario actual

**Entregables:**
- PWA Admin desplegada
- Documentación de usuario
- Manual de uso

---

### FASE 5: PWA CLIENTE ⏱️ 1 semana | 🔴 ALTA

**Objetivo:** App pública para pedidos online

**Tickets:**
1. **CLIENT-MENU**: Catálogo público
   - Vista de categorías
   - Vista de productos
   - Product builder con modificadores

2. **CLIENT-CART**: Carrito inteligente
   - Agrupación de ítems
   - Cálculo en tiempo real
   - Edición de items

3. **CLIENT-CHECKOUT**: Checkout
   - Selector de tipo de pedido
   - Formularios dinámicos
   - Confirmación

4. **CLIENT-TRACKING**: Tracking en tiempo real
   - Timeline de estados
   - WebSockets
   - Mapa para domicilios

**Entregables:**
- PWA Cliente desplegada
- Sistema de QR codes
- Documentación

---

### FASE 6: REPORTES AVANZADOS ⏱️ 0.5 semanas | 🟡 MEDIA

**Objetivo:** Análisis y reportes detallados

**Tickets:**
1. **REPORTS-ADVANCED**: Reportes complejos
   - Ventas por período
   - Análisis de productos
   - Costos vs ingresos

2. **REPORTS-EXPORT**: Exportación
   - PDF
   - Excel
   - CSV

3. **REPORTS-DASHBOARD**: Dashboard ejecutivo
   - Métricas consolidadas
   - Comparativas
   - Proyecciones

**Entregables:**
- Suite de reportes completa
- Dashboard ejecutivo
- Sistema de exportación

---

### FASE 7: QA Y DEPLOY ⏱️ 1 semana | 🔴 CRÍTICA

**Objetivo:** Sistema listo para producción

**Tickets:**
1. **QA-UNIT**: Tests unitarios
   - Coverage > 80%
   - Tests de servicios críticos

2. **QA-INTEGRATION**: Tests de integración
   - Flujos completos
   - Tests multi-tenant

3. **QA-E2E**: Tests end-to-end
   - Cypress/Playwright
   - Flujos de usuario

4. **DEPLOY-PROD**: Deploy a producción
   - Configuración de VPS
   - CI/CD con GitHub Actions
   - Monitoreo

5. **DOCS**: Documentación
   - Manual de usuario
   - Manual de administrador
   - Documentación técnica

**Entregables:**
- Sistema en producción
- Tests pasando
- Documentación completa

---

## 12. CRITERIOS DE CALIDAD Y ACEPTACIÓN

### 12.1 Criterios Funcionales

#### ✅ Autenticación y Seguridad
- [ ] Usuario puede registrar su negocio en < 2 minutos
- [ ] Login funciona con JWT multi-tenant
- [ ] Ningún negocio puede ver datos de otro
- [ ] RBAC valida permisos correctamente
- [ ] Tokens expiran y se renuevan automáticamente

#### ✅ Pedidos
- [ ] Cajero puede crear pedido en < 30 segundos
- [ ] Pedido llega a cocina en < 5 segundos
- [ ] Consecutivos son únicos por sucursal
- [ ] Total calculado en backend es correcto
- [ ] Modificadores suman correctamente al total
- [ ] Inventario se descuenta automáticamente

#### ✅ Impresión
- [ ] Comanda se imprime en < 10 segundos
- [ ] Circuit breaker activa fallback tras 5 fallos
- [ ] Pantalla de cocina recibe pedidos si impresora falla
- [ ] Sistema no se bloquea durante impresión

#### ✅ Inventario
- [ ] Entrada de insumo incrementa stock correctamente
- [ ] Venta descuenta stock de sucursal correcta
- [ ] Alerta se genera cuando stock < mínimo
- [ ] Costos se calculan con promedio ponderado

#### ✅ Domiciliarios
- [ ] Domiciliario puede login y ver pedidos asignados
- [ ] GPS actualiza ubicación cada 30 segundos
- [ ] Cliente puede ver ubicación en tiempo real
- [ ] Entrega valida proximidad al destino

#### ✅ Caja
- [ ] Cierre de caja calcula totales correctamente
- [ ] Diferencias se registran en auditoría
- [ ] Reportes muestran datos precisos

#### ✅ PWA Cliente
- [ ] Cliente puede ver menú sin registro
- [ ] Modificadores funcionan correctamente
- [ ] Carrito agrupa ítems idénticos
- [ ] Tracking muestra estado en tiempo real

### 12.2 Criterios No Funcionales

#### ⚡ Performance
- [ ] Respuesta < 1s en endpoints críticos
- [ ] Soporta 100+ pedidos/hora sin degradación
- [ ] WebSockets mantienen conexión estable
- [ ] Cache Redis reduce queries a DB en 70%

#### 🔒 Seguridad
- [ ] Todas las comunicaciones usan HTTPS
- [ ] Contraseñas hasheadas con bcrypt
- [ ] JWT firmados y verificados correctamente
- [ ] Sin fugas de datos entre negocios (tests pasando)

#### 📊 Escalabilidad
- [ ] Sistema soporta 10 negocios simultáneos
- [ ] Workers escalan automáticamente
- [ ] DB optimizada con índices correctos
- [ ] Frontend usa lazy loading

#### 🛡️ Resiliencia
- [ ] Circuit breaker funciona correctamente
- [ ] Sistema tiene degradación elegante
- [ ] Logs estructurados permiten debugging
- [ ] Backups automáticos funcionan

#### 📱 UX
- [ ] PWA instalable en móvil
- [ ] Interfaz responsive en todos los tamaños
- [ ] Feedback visual en todas las acciones
- [ ] Notificaciones en tiempo real funcionan

---

## 13. INFRAESTRUCTURA Y ESCALAMIENTO

### 13.1 Costos por Etapa

#### MVP (1-10 negocios)
```
VPS Contabo (4GB RAM, 2 vCPU)      $6 USD/mes
PostgreSQL (en mismo VPS)           incluido
Redis (en mismo VPS)                incluido
Dominio fastops.com                 $12 USD/año ($1/mes)
Vercel Pro (frontend)               $20 USD/mes
Email SendGrid (free tier)          gratis

TOTAL MENSUAL: ~$27 USD = ~110.000 COP/mes
```

#### Crecimiento (10-50 negocios)
```
VPS Hetzner (8GB RAM, 4 vCPU)      $12 USD/mes
PostgreSQL (mismo VPS)              incluido
Redis (mismo VPS)                   incluido
Dominio                             $1 USD/mes
Vercel Pro                          $20 USD/mes
Cloudflare Pro (CDN)                $20 USD/mes
SendGrid (Essentials)               $15 USD/mes

TOTAL MENSUAL: ~$68 USD = ~280.000 COP/mes
```

#### Escalado (50-200 negocios)
```
VPS Hetzner (16GB RAM, 8 vCPU)     $25 USD/mes
PostgreSQL Cloud (Supabase)         $25 USD/mes
Redis Cloud (Upstash)               $10 USD/mes
Cloudflare Pro                      $20 USD/mes
Vercel Pro                          $20 USD/mes
Sentry (Team)                       $26 USD/mes
SendGrid (Advanced)                 $30 USD/mes

TOTAL MENSUAL: ~$156 USD = ~640.000 COP/mes
```

### 13.2 Proyección de Ingresos
```
Escenario conservador (50 clientes):
- 15 en Trial (gratis)           = $0
- 20 en Basic ($40.000)          = $800.000
- 15 en Premium ($80.000)        = $1.200.000

INGRESO MENSUAL: $2.000.000 COP
COSTOS: $280.000 COP
MARGEN: $1.720.000 COP (86%)

Escenario optimista (200 clientes):
- 30 en Trial                    = $0
- 100 en Basic                   = $4.000.000
- 70 en Premium                  = $5.600.000

INGRESO MENSUAL: $9.600.000 COP
COSTOS: $640.000 COP
MARGEN: $8.960.000 COP (93%)
```

### 13.3 Plan de Escalamiento

#### Señales para escalar:
1. **CPU > 70%** durante 1 hora → Aumentar vCPU
2. **Memoria > 80%** → Aumentar RAM
3. **Cola > 50 pedidos** → Aumentar workers
4. **Latencia > 2s** → Optimizar queries o escalar DB
5. **10+ negocios nuevos/mes** → Considerar separar servicios

#### Estrategia de escalamiento:
```
Fase 1 (1-10 negocios):
└── Todo en un VPS

Fase 2 (10-50 negocios):
├── Backend en VPS
├── Redis en VPS
└── PostgreSQL en VPS

Fase 3 (50-200 negocios):
├── Backend en VPS (escalable)
├── PostgreSQL Cloud (managed)
├── Redis Cloud (managed)
└── CDN para assets

Fase 4 (200+ negocios):
├── Backend en Kubernetes
├── PostgreSQL cluster
├── Redis cluster
├── Workers independientes
└── Load balancer
13.4 Monitoreo y Alertas
python
# backend/app/monitoring/alerts.py
ALERT_THRESHOLDS = {
    'cpu_percent': 70,
    'memory_percent': 80,
    'disk_percent': 85,
    'queue_size': 50,
    'response_time_ms': 2000,
    'error_rate_percent': 5
}

async def check_system_health():
    """
    Verificar salud del sistema y generar alertas
    """
    metrics = {
        'cpu': psutil.cpu_percent(),
        'memory': psutil.virtual_memory().percent,
        'disk': psutil.disk_usage('/').percent,
        'queue': await get_queue_size(),
        'response_time': await get_avg_response_time(),
        'errors': await get_error_rate()
    }
    
    alerts = []
    
    for key, value in metrics.items():
        threshold_key = f"{key}_percent" if not key.endswith('_size') else key
        threshold = ALERT_THRESHOLDS.get(threshold_key)
        
        if threshold and value > threshold:
            alerts.append({
                'metric': key,
                'value': value,
                'threshold': threshold,
                'severity': 'high' if value > threshold * 1.2 else 'medium'
            })
    
    if alerts:
        await notify_admins(alerts)
    
    return metrics, alerts
________________________________________
📝 RESUMEN EJECUTIVO
FastOps V4.0 es un sistema completo y productizado para salchipapererías que elimina completamente la dependencia de WhatsApp y papel, digitalizando el 100% de las operaciones.
Características principales:
•	✅ Multi-tenant nativo desde el inicio
•	✅ Sistema RBAC avanzado con cache
•	✅ Cola de impresión asíncrona sin bloqueos
•	✅ PWA Cliente para pedidos online
•	✅ WebSockets para tiempo real
•	✅ Domiciliarios con GPS
•	✅ Inventario automático con recetas
•	✅ Modificadores (extras/exclusiones)
•	✅ Reportes avanzados
Timeline estimado MVP:
•	Fase 0.5: 2 días
•	Fase 1: 1.5 semanas
•	Fase 2: 1 semana
•	Fase 3: 1 semana
•	Fase 4: 2 semanas
•	Fase 5: 1 semana
•	Fase 6: 0.5 semanas
•	Fase 7: 1 semana
Total: 8.5 semanas (~2 meses)
Inversión inicial: ~$110.000 COP/mes Ingreso proyectado (50 clientes): ~$2.000.000 COP/mes Margen: 86%

