# 📚 CONCEPTOS APRENDIDOS - TICKET 4.1: CRUD DE PRODUCTOS

## 🎯 OBJETIVO DEL TICKET
Implementar módulo de Gestión de Productos siguiendo arquitectura Repository + Service Layer con multi-tenancy completo.

---

## 🔑 CONCEPTOS CLAVE A DOMINAR

### 1. **SQLModel - Modelos con Validación Automática**
**¿Qué es?**: ORM moderno que combina SQLAlchemy + Pydantic para modelos de BD con validación automática.

**Conceptos importantes:**
- `Field()` para configuraciones de columna
- `Relationship()` para foreign keys
- `default=None` vs `default_factory` para valores por defecto
- Índices con `sa_index=True`
- Constraints únicos con `sa_unique=True`

**Patrón aprendido:**
```python
class Product(SQLModel, table=True):
    # Campos básicos
    name: str = Field(max_length=200)
    price: Decimal = Field(default=0, max_digits=12, decimal_places=2)

    # Relaciones
    category_id: int = Field(foreign_key="categories.id")
    category: Optional["Category"] = Relationship()

    # Multi-tenancy
    company_id: int = Field(foreign_key="companies.id")

    # Soft delete
    is_active: bool = Field(default=True)

    # Metadata de tabla
    __table_args__ = (
        UniqueConstraint("company_id", "name", name="uq_products_company_name"),
        Index("idx_products_company_active", "company_id", "is_active"),
    )
```

---

### 2. **Pydantic Schemas - Validación y Serialización**
**¿Por qué?**: Separar validación de entrada de modelos de BD.

**Tipos de schemas:**
- `Create`: Para creación (sin campos auto-generados)
- `Update`: Para actualizaciones (campos opcionales)
- `Read`: Para respuestas (con relaciones)
- `Response`: Para respuestas API (sin datos sensibles)

**Conceptos importantes:**
- `Field(alias="db_field")` para mapear nombres
- `Optional[]` vs campos requeridos
- `validator()` para validaciones custom
- `ConfigDict` para configuración del schema

**Patrón aprendido:**
```python
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    price: Decimal = Field(..., gt=0)

    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return v

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[Decimal] = None
    is_active: Optional[bool] = None
```

---

### 3. **Patrón Repository - Abstracción de Datos**
**¿Por qué?**: Separar lógica de acceso a BD del negocio.

**Herencia de BaseRepository:**
- Métodos genéricos heredados: `get_by_id()`, `list()`, `create()`, `update()`, `delete()`
- Métodos específicos: `get_by_category()`, `decrement_stock()`

**Conceptos importantes:**
- Dependency injection con `db: AsyncSession`
- Filtros automáticos de multi-tenancy
- Queries optimizadas con joins
- Manejo de concurrencia

**Patrón aprendido:**
```python
class ProductRepository(BaseRepository[Product]):
    async def get_by_category(self, company_id: int, category_id: int) -> List[Product]:
        result = await self.db.execute(
            select(Product).where(
                Product.company_id == company_id,
                Product.category_id == category_id,
                Product.is_active == True
            )
        )
        return result.scalars().all()
```

---

### 4. **Patrón Service Layer - Lógica de Negocio**
**¿Por qué?**: Centralizar reglas de negocio, validaciones, integraciones.

**Responsabilidades:**
- Validar entrada vs reglas de negocio
- Coordenar operaciones entre repositorios
- Manejar transacciones complejas
- Integrar con servicios externos
- Aplicar permisos y autorizaciones

**Conceptos importantes:**
- Métodos async para operaciones I/O
- Validación cross-tenant (verificar ownership)
- Manejo de errores personalizado
- Transacciones con `async with db.begin():`

**Patrón aprendido:**
```python
class ProductService:
    def __init__(self, repo: ProductRepository):
        self.repo = repo

    async def create_product(self, product_data: ProductCreate, company_id: int) -> Product:
        # 1. Validar unicidad de nombre por empresa
        # 2. Verificar que category_id pertenece a la empresa
        # 3. Crear producto
        # 4. Retornar producto creado
```

---

### 5. **FastAPI Routers - Endpoints RESTful**
**¿Por qué?**: Exponer API REST con validación automática.

**Estructura del router:**
- Prefijo: `/products`
- Tags para documentación
- Dependencias de autenticación
- Validación automática con schemas
- Manejo de errores consistente

**Conceptos importantes:**
- `@router.post()`, `@router.get()`, etc.
- `Depends()` para inyección de dependencias
- `status_code` para códigos HTTP apropiados
- `response_model` para documentación automática

**Patrón aprendido:**
```python
@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(
    product: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Validaciones y creación
    pass
```

---

### 6. **RBAC - Role Based Access Control**
**¿Por qué?**: Control granular de permisos por acción.

**Permisos definidos:**
- `products.read` - Ver productos
- `products.create` - Crear productos
- `products.update` - Actualizar productos
- `products.delete` - Eliminar productos

**Conceptos importantes:**
- Decoradores `@require_permission('products.create')`
- Verificación automática en cada endpoint
- Mensajes de error consistentes
- Jerarquía de roles (admin > cajero > cocina)

---

### 7. **Soft Delete - Eliminación Lógica**
**¿Por qué?**: Preservar integridad referencial, auditoría.

**Implementación:**
- Campo `is_active: bool = Field(default=True)`
- Queries filtran `is_active == True` automáticamente
- "Eliminación" = `UPDATE ... SET is_active = False`
- Restauración posible si es necesario

**Conceptos importantes:**
- Índices incluyen `is_active` para performance
- Foreign keys pueden referenciar registros "eliminados"
- Auditoría mantiene historial completo

---

### 8. **Validación Cross-Tenant**
**¿Por qué?**: Prevenir acceso no autorizado entre empresas.

**Verificaciones necesarias:**
- `category_id` debe pertenecer a `company_id` del usuario
- Producto debe ser de la empresa del usuario
- Relaciones deben ser consistentes

**Patrón aprendido:**
```python
# Verificar que la categoría pertenece a la empresa
category = await category_repo.get_by_id(category_id, company_id)
if not category:
    raise HTTPException(400, "Category does not belong to your company")
```

---

### 9. **Gestión de Imágenes (Placeholder)**
**¿Por qué?**: Los productos necesitan imágenes para el menú.

**Estrategia:**
- Campo `image_url: Optional[str]`
- Placeholder para futura implementación
- Validación de tipo MIME
- Upload a CDN (Cloudinary, AWS S3, etc.)

**Conceptos futuros:**
- `UploadFile` de FastAPI
- Validación de archivos
- Procesamiento de imágenes
- URLs seguras con expiración

---

### 10. **Transacciones y Concurrencia**
**¿Por qué?**: Operaciones atómicas en BD.

**Conceptos importantes:**
- `async with db.begin():` para transacciones
- Locks optimistas vs pesimistas
- Manejo de `IntegrityError`
- Rollback automático en errores

**Patrón aprendido:**
```python
async with db.begin():
    # Operaciones atómicas
    product = await repo.create(product_data)
    await inventory_service.adjust_stock(...)  # Si hay receta
```

---

## 🚀 PASOS DE IMPLEMENTACIÓN DETALLADOS

### Paso 1: Modelo Product
**Archivo:** `backend/app/models/product.py`

**Campos requeridos:**
- `id`: Primary key auto-increment
- `company_id`: Foreign key a companies (multi-tenant)
- `category_id`: Foreign key a categories (opcional)
- `name`: String único por empresa
- `description`: Text opcional
- `price`: Decimal con precisión financiera
- `stock`: Decimal opcional (inventario)
- `image_url`: String opcional
- `is_active`: Boolean para soft delete
- `tax_rate`: Decimal para impuestos
- Timestamps: created_at, updated_at

**Relaciones:**
- `category: Optional[Category]` - Lazy loading
- `company: Company` - Para acceso directo

**Índices críticos:**
- `(company_id, name)` - Unicidad
- `(company_id, category_id)` - Filtros por categoría
- `(company_id, is_active)` - Listados activos

### Paso 2: Esquemas Pydantic
**Archivo:** `backend/app/schemas/product.py`

**ProductCreate:**
- Campos requeridos: name, price
- Campos opcionales: description, category_id, stock, tax_rate
- Validadores: price > 0, name no vacío

**ProductUpdate:**
- Todos los campos opcionales
- Validadores condicionales

**ProductRead:**
- Incluye relaciones: category.name
- Excluye campos internos

**ProductResponse:**
- Para respuestas API
- Campos calculados si es necesario

### Paso 3: Repository
**Archivo:** `backend/app/repositories/product_repository.py`

**Heredar de BaseRepository:**
```python
class ProductRepository(BaseRepository[Product]):
    # Constructor estándar
    def __init__(self, db: AsyncSession):
        super().__init__(Product, db)
```

**Métodos específicos:**
- `get_active_by_company(company_id: int)`
- `get_by_category(company_id: int, category_id: int)`
- `decrement_stock(product_id: int, quantity: Decimal)` - Para ventas
- `search_by_name(company_id: int, query: str)`

### Paso 4: Service
**Archivo:** `backend/app/services/product_service.py`

**Métodos principales:**
- `create_product(data: ProductCreate, company_id: int) -> Product`
- `update_product(product_id: int, data: ProductUpdate, company_id: int) -> Product`
- `delete_product(product_id: int, company_id: int) -> bool`
- `list_products(company_id: int, filters: dict) -> List[Product]`

**Validaciones de negocio:**
- Unicidad de nombre por empresa
- Verificación de categoría ownership
- Límites de precio y stock
- Integridad de datos

### Paso 5: Router
**Archivo:** `backend/app/routers/product.py`

**Endpoints:**
- `GET /products` - Listar con filtros
- `POST /products` - Crear
- `GET /products/{id}` - Detalle
- `PUT /products/{id}` - Actualizar
- `DELETE /products/{id}` - Soft delete

**Decoradores de permisos:**
```python
@router.post("/", dependencies=[Depends(require_permission("products.create"))])
```

### Paso 6: Integración al Sistema
**Archivos a modificar:**
- `backend/app/models/__init__.py` - Importar Product
- `backend/app/routers/__init__.py` - Registrar router
- `backend/app/main.py` - Incluir router
- Migraciones: `alembic revision --autogenerate`

---

## 📋 CHECKLIST DE IMPLEMENTACIÓN

### ✅ Modelo Product
- [ ] Campos definidos correctamente
- [ ] Relaciones configuradas
- [ ] Índices optimizados
- [ ] Constraints únicos
- [ ] Soft delete implementado

### ✅ Esquemas Pydantic
- [ ] ProductCreate con validaciones
- [ ] ProductUpdate con campos opcionales
- [ ] ProductRead con relaciones
- [ ] ProductResponse optimizado

### ✅ Repository
- [ ] Herencia de BaseRepository
- [ ] Métodos específicos implementados
- [ ] Queries optimizadas
- [ ] Filtros multi-tenant automáticos

### ✅ Service
- [ ] Validaciones de negocio
- [ ] Verificación cross-tenant
- [ ] Manejo de errores
- [ ] Transacciones apropiadas

### ✅ Router
- [ ] Endpoints RESTful
- [ ] Permisos RBAC aplicados
- [ ] Validación automática
- [ ] Manejo de errores consistente

### ✅ Integración
- [ ] Modelo registrado en __init__.py
- [ ] Router incluido en main.py
- [ ] Migración generada y aplicada
- [ ] Tests básicos funcionales

---

## 🎯 RESULTADO ESPERADO

Después de completar este ticket, tendrás:

1. **Sistema completo de productos** multi-tenant
2. **API RESTful** con documentación automática
3. **Validaciones robustas** de negocio y datos
4. **Seguridad granular** con RBAC
5. **Código mantenible** siguiendo mejores prácticas
6. **Base sólida** para módulos futuros (pedidos, inventario)

**El negocio podrá:**
- Gestionar su catálogo de productos de forma segura
- Mantener productos aislados por empresa
- Aplicar validaciones de negocio automáticas
- Integrar con otros módulos (pedidos, inventario)

**Como desarrollador dominarás:**
- Arquitectura limpia con separación de responsabilidades
- SQLModel avanzado con relaciones complejas
- Pydantic schemas profesionales
- Patrones Repository + Service Layer
- FastAPI con validación automática
- RBAC granular en APIs REST
