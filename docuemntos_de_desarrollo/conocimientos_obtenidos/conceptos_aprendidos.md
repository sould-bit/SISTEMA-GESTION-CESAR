# 📚 Conceptos Aprendidos - SISALCHI

## Índices en Bases de Datos

### ¿Qué es un índice?
Un índice es una estructura de datos que acelera las búsquedas en una tabla. Sin índice, la DB debe revisar TODA la tabla (table scan). Con índice, va directamente a los registros que coinciden.

### Tipos de índices aprendidos:

#### 1. Índice Simple (`index=True`)
```python
company_id: int = Field(foreign_key="companies.id", index=True)
```
- Se define directamente en el Field
- Indexa UNA sola columna
- SQLAlchemy genera nombre automático

#### 2. Índice Compuesto (`Index()` en `__table_args__`)
```python
from sqlalchemy import Index

__table_args__ = (
    Index("idx_branches_active", "company_id", "is_active"),
)
```
- Se define en `__table_args__`
- Indexa MÚLTIPLES columnas juntas
- Tú controlas el nombre
- Optimiza queries que filtran por TODAS las columnas del índice

### ¿Cuándo usar índice compuesto?
En sistemas **multi-tenant**, casi siempre filtras por `company_id` + otra cosa:
```sql
SELECT * FROM branches WHERE company_id = 5 AND is_active = true;
```
El índice `(company_id, is_active)` hace esta consulta muy rápida.

### Regla para multi-tenant:
> En tablas que pertenecen a un negocio, siempre incluye `company_id` en índices compuestos.

---

---

## 🏗️ Arquitectura Recomendada para FastOps

### ✅ DECISIÓN: Mantener Arquitectura Monolítica Modular

Basado en el análisis completo del proyecto, **recomiendo mantener la arquitectura monolítica actual** con las siguientes justificaciones:

#### 📊 Estado Actual del Proyecto:
- **Fase:** 0.5 (15% completado)
- **Equipo:** 1 desarrollador principal
- **Alcance:** MVP para salchipaperías SaaS multi-tenant
- **Complejidad:** Backend básico + modelos multi-tenant

#### 🎯 Factores que Favorecen Monolito:

**1. Equipo Pequeño (1 dev)**
- ✅ Desarrollo más rápido sin coordinación entre servicios
- ✅ Menos complejidad de deployment
- ✅ Debugging más sencillo

**2. Producto en Fase Inicial**
- ✅ MVP: Solo funcionalidades core implementadas
- ✅ Cliente único inicialmente
- ✅ Requisitos pueden cambiar rápidamente

**3. SaaS Multi-Tenant Simple**
- ✅ Base de datos única (requisito del negocio)
- ✅ Aislamiento por `company_id`/`branch_id` suficiente
- ✅ Costos de infraestructura bajos ($5/mes VPS)

**4. Requisitos de Rendimiento Moderados**
- ✅ 200 pedidos/día máximo
- ✅ <300ms respuesta (fácil con monolito optimizado)
- ✅ No necesita escalabilidad horizontal por ahora

#### 🚨 Señales de Alerta para Migrar:
- ❌ Más de 3 desarrolladores trabajando
- ❌ Deploy toma >10 minutos
- ❌ Tests tardan >5 minutos
- ❌ 50+ routers/endpoints
- ❌ Costos infraestructura >$50/mes

#### 🛠️ Estrategia de Monolito Modular Recomendada:

```
backend/app/
├── main.py                    # Punto de entrada único
├── models/                    # Todos los modelos juntos
│   ├── company.py            # Multi-tenant core
│   ├── user.py               # Usuarios
│   ├── order.py              # ✅ Próximo: Pedidos
│   ├── product.py            # ✅ Próximo: Productos/Recetas
│   └── inventory.py          # ✅ Próximo: Inventario
├── routers/                   # Routers modulares
│   ├── auth.py               # ✅ Implementado
│   ├── orders.py             # 🔄 Próximo módulo
│   ├── inventory.py          # 🔄 Próximo módulo
│   └── reports.py            # 🔄 Módulo final
├── services/                 # 📁 NUEVO: Lógica de negocio
│   ├── order_service.py      # Reglas de pedidos
│   ├── inventory_service.py  # Gestión de stock
│   └── report_service.py     # Generación de reportes
└── middleware/               # 📁 NUEVO: Seguridad multi-tenant
    └── tenant_middleware.py  # Verificación company_id
```

#### 📈 Plan de Crecimiento:

**Fase 1 (Actual - 0.5):** Monolito básico
- ✅ Modelos multi-tenant
- ✅ Autenticación básica
- 🔄 Routers de pedidos

**Fase 2 (1.0):** Monolito maduro
- 🔄 Todos los routers implementados
- 🔄 Middleware de seguridad completo
- 🔄 Servicios de negocio separados

**Fase 3 (2.0):** Evaluar microservicios
- 🔄 Si el monolito crece mucho (>1000 líneas/main.py)
- 🔄 Si llegan más desarrolladores
- 🔄 Si necesitamos escalabilidad específica

### 🎨 Patrón Recomendado: Clean Architecture en Monolito

```
📁 FastOps Monolito
├── 🏛️ main.py (Framework Layer)
├── 🔄 routers/ (Interface Adapters)
├── 💼 services/ (Use Cases - Lógica de Negocio)
├── 📊 models/ (Entities - Datos)
└── 🔌 utils/ (Infrastructure)
```

**Ventajas:**
- ✅ Separación clara de responsabilidades
- ✅ Fácil testing de cada capa
- ✅ Migración futura a microservicios más sencilla

---

## Arquitectura: Cuándo Migrar a Microservicios Reales

### ¿Qué son Microservicios Reales?
A diferencia de tu arquitectura actual (2 servicios simples: backend + DB), los **microservicios reales** dividen el backend en múltiples servicios independientes, cada uno con:
- **Base de datos propia** (Database per Service pattern)
- **Equipo de desarrollo dedicado**
- **Deploy independiente**
- **Comunicación vía APIs** (HTTP/gRPC)
- **Circuit breakers y service mesh**

### 🎯 Punto 1: "Cuando el monolito crezca mucho"

#### Señales de que el monolito está demasiado grande:

**📈 Crecimiento de Código:**
- `main.py` tiene 1000+ líneas
- Más de 20 routers diferentes
- Models/ tiene 50+ archivos
- Tiempo de build > 10 minutos

**🐌 Problemas de Rendimiento:**
- Endpoints tardan >2 segundos
- Memoria RAM > 2GB en producción
- CPU > 70% constante

**👥 Problemas de Equipo:**
- 5+ desarrolladores trabajando en el mismo código
- Conflictos de merge diarios
- Dificultad para code reviews

#### Ejemplo en tu dominio:
```python
# Tu main.py actual (pequeño):
app.include_router(auth.router)  # Solo 1 router

# Monolito crecido (problema):
app.include_router(auth.router)
app.include_router(orders.router)      # 300 endpoints
app.include_router(inventory.router)   # 150 endpoints
app.include_router(reports.router)     # 200 endpoints
app.include_router(delivery.router)    # 100 endpoints
app.include_router(payments.router)    # 80 endpoints
```

### 👥 Punto 2: "Cuando necesites equipos separados por dominio"

#### ¿Qué es un Bounded Context?
Cada **dominio de negocio** se convierte en un servicio independiente:

**Servicio de Pedidos** (`orders-service`)
- Gestión de mesas, llevar, domicilios
- Estados: pendiente → preparando → listo → entregado
- Consecutivos M-XXX, L-XXX, D-XXX

**Servicio de Inventario** (`inventory-service`)
- Productos y recetas
- Descuento automático de insumos
- Alertas de stock bajo

**Servicio de Domiciliarios** (`delivery-service`)
- Gestión de repartidores
- Asignación automática/manual
- Tracking GPS en tiempo real

#### Ventajas para equipos separados:
```
Equipo A: Solo toca pedidos
├── orders/models/
├── orders/routers/
└── orders/services/

Equipo B: Solo toca inventario
├── inventory/models/
├── inventory/routers/
└── inventory/services/
```

### ⚡ Punto 3: "Cuando requieras escalabilidad independiente"

#### Tipos de Escalabilidad:

**Escalabilidad Vertical:** Más CPU/RAM a una máquina
**Escalabilidad Horizontal:** Más máquinas corriendo el mismo código

#### Ejemplo en FastOps:

**Inventario:** Se consulta mucho pero cambia poco
- ✅ Puede correr en 1-2 servidores pequeños
- ✅ Base de datos de solo lectura posible

**Pedidos en hora pico:** 200 pedidos/hora
- 🔥 Necesita auto-scaling (2-10 servidores según demanda)
- 🔥 Base de datos dedicada con réplicas de lectura

**Reportes:** Se ejecutan al final del día
- ⏰ Pueden correr en horario programado
- ⏰ Servidores spot/baratos

### 🚨 Señales de que necesitas escalabilidad independiente:

**Problemas de Contención:**
- Pedidos lentos porque reportes pesados bloquean la DB
- Inventario lento porque pedidos masivos saturan CPU

**Costos Innecesarios:**
- Pagar servidores grandes para todo el sistema cuando solo pedidos necesita scale

**Disponibilidad:**
- Si inventario se cae, pedidos siguen funcionando
- Si reportes fallan, no afectan operaciones críticas

### 📊 Matriz de Decisión para FastOps:

| Servicio | Tamaño Actual | Equipos | Escalabilidad | Urgencia |
|----------|---------------|---------|---------------|----------|
| Auth     | Pequeño       | 1 dev   | Compartida    | Baja     |
| Orders   | Creciendo     | 2 devs  | Alta demanda | Alta     |
| Inventory| Mediano       | 1 dev   | Media        | Media    |
| Reports  | Grande        | 1 dev   | Batch        | Media    |
| Delivery | Pequeño       | 1 dev   | GPS tracking | Media    |

### 🛠️ Estrategia de Migración Recomendada:

#### Fase 1: Separar por Dominio (Strangler Pattern)
```
Monolito Actual
├── auth/
├── orders/     ← Extraer primero
├── inventory/
├── reports/
└── delivery/
```

#### Fase 2: Database per Service
```
Antes: 1 base de datos para todo
Después:
├── orders_db    (PostgreSQL)
├── inventory_db (PostgreSQL)  
└── auth_db      (PostgreSQL/MySQL)
```

#### Fase 3: API Gateway + Service Mesh
```
Cliente → API Gateway → Services
                    ↓
             Service Discovery
                    ↓
            Circuit Breakers
```

## 📋 Evaluación Técnica del Backend

### Documento de Evaluación Completo
Se creó `backend/EVALUACION_TECNICA_BACKEND.md` - documento vivo que evalúa:

#### ✅ Fortalezas Identificadas:
- **Arquitectura monolítica modular** bien estructurada
- **Modelos SQLModel multi-tenant** correctamente diseñados
- **Estructura profesional** de directorios
- **Configuración Docker** apropiada

#### 🔴 Problemas Críticos Detectados:
1. **Sintaxis Pydantic v1 obsoleta** - `class Config` debe ser `model_config`
2. **Configuración Settings incorrecta** - no lee variables de entorno
3. **Falta middleware multi-tenant** - riesgo de seguridad
4. **Ausencia de servicios de negocio** - lógica mezclada en routers

#### 🟡 Problemas de Alta Prioridad:
- Manejo de errores inconsistente
- Falta de logging estructurado
- Ausencia de tests automatizados
- Validaciones insuficientes en schemas

### Ruta Crítica de Mejora:
1. **Fase 1:** Resolver problemas Pydantic v2 (CRÍTICO)
2. **Fase 2:** Implementar seguridad multi-tenant
3. **Fase 3:** Crear capa de servicios
4. **Fase 4:** Tests y documentación

## Próximos conceptos por aprender:
- [ ] Pydantic v2 Migration Guide completo
- [ ] FastAPI Middleware patterns
- [ ] Service Layer Pattern
- [ ] Repository Pattern con SQLModel
- [ ] Testing con pytest-asyncio
- [ ] Structured Logging con loguru
- [ ] Alembic y migraciones de base de datos
- [ ] JWT Multi-tenant avanzado
- [ ] FastAPI Dependency Injection avanzada
- [ ] API Gateway patterns
