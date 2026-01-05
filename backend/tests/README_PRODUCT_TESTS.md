# 🧪 **DOCUMENTO DE APRENDIZAJE: TESTS COMPLETOS PARA PRODUCTOS**

## **🎯 PROPÓSITO**

Este documento registra todos los conceptos importantes aprendidos durante la implementación completa de tests para el módulo de **Gestión de Productos** (Ticket 4.1). El objetivo es convertirte en un **Tony Stark del testing** en aplicaciones FastAPI con SQLModel.

---

## **🏗️ ARQUITECTURA DE TESTS IMPLEMENTADA**

### **1. Estructura de Tests por Capas**

```
tests/
├── conftest.py                 # ⚙️ Configuración global y fixtures
├── unit/                       # 🔬 Tests unitarios
│   └── test_product_schemas.py # 📋 Validaciones Pydantic
├── integration/                # 🔗 Tests de integración
│   ├── test_product_crud_integration.py    # 🔄 CRUD completo
│   ├── test_product_concurrency.py         # ⚡ Concurrencia
│   ├── test_product_multi_tenant.py        # 🏢 Multi-tenancy
│   └── test_product_router.py              # 🌐 Endpoints API
└── services/                   # 🏭 Tests de servicios
    └── test_product_service.py # 🔧 Lógica de negocio
repositories/                   # 💾 Tests de repositorio
    └── test_product_repository.py # 🗄️ Acceso a datos
```

### **2. Tipos de Tests Implementados**

#### **🧪 UNITARIOS (pytest.mark.unit)**
- **Aislamiento completo**: Mock de dependencias externas
- **Validaciones individuales**: Una función/método por test
- **Patrón AAA**: Arrange-Act-Assert claramente separado
- **Cobertura específica**: Validaciones de negocio, esquemas, lógica pura

#### **🔗 INTEGRACIÓN (pytest.mark.integration)**
- **Múltiples capas**: Service + Repository + Base de datos
- **Flujos completos**: CRUD end-to-end
- **Validaciones reales**: Sin mocks, BD real
- **Escenarios complejos**: Concurrencia, multi-tenancy

#### **⚡ STRESS TESTING (pytest.mark.integration)**
- **asyncio.gather()**: Simulación de múltiples usuarios concurrentes
- **Race conditions**: Detección de problemas de concurrencia
- **Performance**: Validación de tiempos de respuesta
- **Isolation**: Transacciones independientes

---

## **📚 CONCEPTOS TÉCNICOS DOMINADOS**

### **1. 🏭 TESTING DE SERVICIOS (ProductService)**

#### **Validaciones de Precio**
```python
# ✅ PRECIO POSITIVO
def test_create_product_price_must_be_positive():
    with pytest.raises(HTTPException) as exc_info:
        await service.create_product({"price": Decimal('0')}, company_id)
    assert "Precio debe ser mayor a cero" in str(exc_info.value)

# ✅ PRECIO MÁXIMO
def test_create_product_price_maximum_validation():
    with pytest.raises(ValidationError) as exc_info:
        ProductCreate(price=Decimal('1000001.00'))  # > 1M
    assert "Precio no puede exceder" in str(exc_info.value)
```

#### **Unicidad de Nombre por Empresa**
```python
# ✅ UNICIDAD POR TENANT
async def test_create_product_unique_name_per_company():
    # Crear primer producto
    await service.create_product({"name": "Único"}, company_1.id)

    # Intentar duplicado en misma empresa (FALLA)
    with pytest.raises(HTTPException) as exc_info:
        await service.create_product({"name": "Único"}, company_1.id)
    assert "Ya existe un producto" in str(exc_info.value)

    # Pero funciona en empresa diferente
    await service.create_product({"name": "Único"}, company_2.id)  # ✅
```

#### **Validación Anti-Cross-Tenant**
```python
# ✅ VALIDACIÓN DE PROPIEDAD DE CATEGORÍA
async def _validate_category_ownership(self, category_id, company_id):
    result = await self.db.execute(
        select(Category).where(
            Category.id == category_id,
            Category.company_id == company_id,  # 🔐 CLAVE: Validar ownership
            Category.is_active == True
        )
    )
    if not category:
        raise HTTPException(400, "no pertenece a su empresa")
```

### **2. 🗄️ TESTING DE REPOSITORIOS (ProductRepository)**

#### **Operaciones CRUD Básicas**
```python
# ✅ CREATE
async def test_create_product(self, repo, company, category):
    product_dict = {"name": "Test", "price": Decimal('10.00'), ...}
    product = await repo.create(product_dict)
    assert product.company_id == company.id

# ✅ READ
async def test_get_by_id_or_404_found(self, repo, product):
    found = await repo.get_by_id_or_404(product.id, product.company_id)
    assert found.name == product.name
```

#### **Consultas Específicas con Multi-Tenancy**
```python
# ✅ FILTRADO AUTOMÁTICO POR COMPANY_ID
async def get_active_by_category(self, company_id: int, category_id: int):
    result = await self.db.execute(
        select(Product).where(
            and_(
                Product.company_id == company_id,  # 🔐 AISLAMIENTO
                Product.category_id == category_id,
                Product.is_active == True
            )
        )
    )
    return result.scalars().all()
```

#### **Búsqueda Insensible a Mayúsculas**
```python
# ✅ CASE INSENSITIVE SEARCH
async def search_by_name(self, company_id: int, query: str, limit: int = 50):
    search_pattern = f"%{query}%"
    result = await self.db.execute(
        select(Product).where(
            and_(
                Product.company_id == company_id,  # 🔐 TENANT ISOLATION
                Product.is_active == True,
                func.lower(Product.name).like(func.lower(search_pattern))
            )
        ).limit(limit)
    )
    return result.scalars().all()
```

### **3. ⚡ TESTING DE CONCURRENCIA**

#### **Simulación de Múltiples Usuarios**
```python
# ✅ STRESS TESTING CON asyncio.gather
async def test_concurrent_product_creation():
    num_concurrent = 10
    async def create_task(task_id: int):
        return await service.create_product({
            "name": f"Producto Concurrente {task_id}",
            "price": Decimal('10.00')
        }, company_id)

    # 🔥 SIMULAR 10 USUARIOS CREANDO AL MISMO TIEMPO
    tasks = [create_task(i) for i in range(num_concurrent)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # ✅ TODAS DEBEN SER EXITOSAS (nombres únicos)
    successful = [r for r in results if not isinstance(r, Exception)]
    assert len(successful) == num_concurrent
```

#### **Race Conditions en Stock**
```python
# ✅ DETECCIÓN DE RACE CONDITIONS
async def test_concurrent_stock_update_race_condition():
    # Crear producto con stock inicial
    product = await service.create_product({"stock": Decimal('100')}, company_id)

    # 🔥 MÚLTIPLES ACTUALIZACIONES SIMULTÁNEAS
    num_updates = 5
    stock_increments = [10, 15, -5, 8, -12]

    async def update_task(increment):
        current = product.stock
        return await service.update_stock(product.id, company_id, current + increment)

    tasks = [update_task(inc) for inc in stock_increments]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # ✅ STOCK FINAL CORRECTO (sin pérdida de actualizaciones)
    final_product = await repo.get_by_id_or_404(product.id, company_id)
    expected_final = Decimal('100') + sum(stock_increments)
    assert final_product.stock == expected_final
```

### **4. 🏢 TESTING DE MULTI-TENANCY**

#### **Aislamiento Total por Empresa**
```python
# ✅ EMPRESA A ≠ EMPRESA B
async def test_tenant_isolation_create_products():
    # Empresa 1 crea producto
    product_1 = await service.create_product(data, company_1.id)

    # Empresa 2 crea producto con mismo nombre
    product_2 = await service.create_product(data, company_2.id)  # ✅ FUNCIONA

    # Empresa 1 lista productos
    products_1 = await service.get_products(company_1.id)
    names_1 = [p.name for p in products_1]

    # Empresa 2 lista productos
    products_2 = await service.get_products(company_2.id)
    names_2 = [p.name for p in products_2]

    # 🔐 AISLAMIENTO COMPLETO
    assert product_1.name not in names_2
    assert product_2.name not in names_1
```

#### **Prevención de Cross-Tenant Attacks**
```python
# ✅ PREVENCIÓN DE ATAQUES CROSS-TENANT
async def test_tenant_isolation_cross_company_operations():
    # Crear producto en Empresa 1
    product_1 = await service.create_product(data, company_1.id)

    # Usuario malicioso de Empresa 2 conoce el ID
    malicious_company_id = company_2.id
    known_product_id = product_1.id

    # ❌ INTENTO DE ACCESO NO AUTORIZADO
    with pytest.raises(HTTPException) as exc_info:
        await repo.get_by_id_or_404(known_product_id, malicious_company_id)
    assert exc_info.value.status_code == 404  # 👻 NO ENCONTRADO

    with pytest.raises(HTTPException) as exc_info:
        await service.update_product(known_product_id, update_data, malicious_company_id)
    assert exc_info.value.status_code == 404  # 👻 NO ENCONTRADO
```

### **5. 📋 TESTING DE ESQUEMAS PYDANTIC**

#### **Validaciones de Campo**
```python
# ✅ VALIDACIÓN DE PRECIO
def test_product_create_price_positive_validation():
    with pytest.raises(ValidationError) as exc_info:
        ProductCreate(name="Test", price=Decimal('0'))
    assert "Precio debe ser mayor a cero" in str(exc_info.value)

# ✅ VALIDACIÓN DE TASA DE IMPUESTO
def test_product_create_tax_rate_over_100_percent_validation():
    with pytest.raises(ValidationError) as exc_info:
        ProductCreate(name="Test", price=Decimal('10'), tax_rate=Decimal('1.5'))
    assert "entre 0% y 100%" in str(exc_info.value)
```

#### **Cálculos Automáticos**
```python
# ✅ PRECIO FINAL CALCULADO AUTOMÁTICAMENTE
def test_product_read_calculate_final_price():
    product = ProductRead(
        id=1, name="Test", price=Decimal('20.00'), tax_rate=Decimal('0.15')
    )
    # precio * (1 + tax_rate) = 20.00 * 1.15 = 23.00
    assert product.final_price == Decimal('23.00')
```

### **6. 🌐 TESTING DE ENDPOINTS API**

#### **Autenticación y Autorización**
```python
# ✅ AUTENTICACIÓN REQUERIDA
async def test_unauthenticated_requests():
    response = await client.get("/products/")
    assert response.status_code == 401  # ❌ NO AUTENTICADO

# ✅ PERMISOS RBAC
async def test_create_product_unauthorized():
    # Usuario SIN permiso products.create
    response = await client.post("/products/", json=data, headers=auth_header)
    assert response.status_code == 403  # ❌ NO AUTORIZADO
    assert "No tienes permiso" in response.json()["detail"]
```

#### **Validaciones End-to-End**
```python
# ✅ VALIDACIONES PYDANTIC EN ENDPOINTS
async def test_validation_errors_in_endpoints():
    invalid_data = {"name": "Test", "price": "-10.00"}  # Precio negativo

    response = await client.post("/products/", json=invalid_data, headers=auth_header)
    assert response.status_code == 422  # ❌ VALIDACIÓN FALLIDA
    assert "price" in str(response.json()["detail"])
```

---

## **🛠️ HERRAMIENTAS Y PATRONES MAESTROS**

### **1. 📊 FIXTURES AVANZADAS**

```python
# ✅ FIXTURES PARA MULTI-TENANCY
@pytest.fixture
async def test_company_2(db_session):
    """Segunda empresa para tests de aislamiento."""
    company = Company(name="Empresa Dos", slug="empresa-dos")
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)
    return company

# ✅ FIXTURES PARA LOTES DE DATOS
@pytest.fixture
async def test_products_batch(db_session, test_company, test_category):
    """Crear lote de productos para tests de performance."""
    products = []
    for i in range(5):
        product = Product(
            name=f"Producto {i+1}",
            price=Decimal(f'{(i+1) * 10}.00'),
            company_id=test_company.id,
            category_id=test_category.id
        )
        products.append(product)
        db_session.add(product)
    await db_session.commit()
    return products
```

### **2. 🎭 MOCKING INTELIGENTE**

```python
# ✅ MOCK DE MÉTODOS PARA AISLAR TESTS
async def test_create_product_success(self, db_session, test_company, test_category):
    service = ProductService(db_session)

    with patch.object(service, '_validate_category_ownership'), \
         patch.object(service, '_check_product_name_unique'):
        # Solo testea la lógica principal, no las validaciones
        result = await service.create_product(valid_data, test_company.id)
        assert result.name == "Producto Test"
```

### **3. 🔄 TESTING ASÍNCRONO AVANZADO**

```python
# ✅ ESPERA DE OPERACIONES ASÍNCRONAS
async def test_concurrent_operations_performance():
    start_time = time.time()

    # 🔥 MÚLTIPLES OPERACIONES SIMULTÁNEAS
    tasks = [create_product_task(i) for i in range(50)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    execution_time = time.time() - start_time

    # ✅ PERFORMANCE ACEPTABLE
    assert execution_time < 10.0  # Menos de 10 segundos para 50 operaciones
```

### **4. 📈 ASSERTIONS ESPECÍFICAS**

```python
# ✅ ASSERTIONS PARA HTTP EXCEPTIONS
with pytest.raises(HTTPException) as exc_info:
    await service.operation()
assert exc_info.value.status_code == 400
assert "mensaje específico" in str(exc_info.value.detail)

# ✅ ASSERTIONS PARA VALIDATION ERRORS
with pytest.raises(ValidationError) as exc_info:
    Schema(**invalid_data)
assert "campo específico" in str(exc_info.value)

# ✅ ASSERTIONS PARA CONCURRENCIA
# Verificar que todas las operaciones fueron exitosas
successful = [r for r in results if not isinstance(r, Exception)]
assert len(successful) == expected_count
```

---

## **🎖️ LOGROS ALCANZADOS**

### **✅ COBERTURA COMPLETA**
- **8 archivos de test** creados
- **Unitarios**: Validaciones, lógica de negocio
- **Integración**: CRUD completo, concurrencia, multi-tenancy
- **API**: Endpoints con autenticación RBAC
- **Esquemas**: Validaciones Pydantic end-to-end

### **✅ CONCEPTOS DOMINADOS**
- 🏭 **Arquitectura de Servicios**: Inyección de dependencias, separación de responsabilidades
- 🗄️ **Patrón Repository**: Abstracción de datos, consultas especializadas
- 🏢 **Multi-Tenancy**: Aislamiento completo, validaciones anti-cross-tenant
- ⚡ **Concurrencia**: Race conditions, asyncio.gather, stress testing
- 📋 **Validaciones**: Pydantic schemas, field validators, cálculos automáticos
- 🌐 **FastAPI**: Endpoints, autenticación, permisos RBAC, responses HTTP
- 🧪 **Testing Avanzado**: Fixtures, mocking, assertions específicas, patrones AAA

### **✅ SEGURIDAD VALIDADA**
- 🔐 **Aislamiento por Empresa**: Empresa A no ve datos de Empresa B
- 🛡️ **Prevención de Cross-Tenant**: Validaciones en todas las operaciones
- 👤 **RBAC Completo**: Permisos granulares, middleware de autorización
- ⚡ **Concurrencia Segura**: No race conditions en operaciones críticas

---

## **🚀 PRÓXIMOS PASOS PARA SER TONY STARK**

### **1. EXPANDIR COBERTURA**
- Tests de carga (Load Testing) con Locust
- Tests de integración con frontend (E2E)
- Tests de performance y memory leaks

### **2. AUTOMATIZACIÓN**
- CI/CD con GitHub Actions
- Cobertura de código con coverage.py
- Reportes automáticos de calidad

### **3. PATRONES AVANZADOS**
- Property-based testing con Hypothesis
- Contract testing con Pact
- Chaos engineering con toxiproxy

---

## **💡 FILOSOFÍA DEL TESTING PROFESIONAL**

> *"El testing no es demostrar que el código funciona, sino asegurarse de que no se rompe cuando menos lo esperas."*

### **🔑 PRINCIPIOS MAESTROS**
1. **Cada bug encontrado en producción cuesta 100x más que en desarrollo**
2. **Los tests son la mejor documentación viva del código**
3. **La calidad se construye, no se inspecciona**
4. **Los tests dan confianza para refactorizar sin miedo**
5. **Un sistema sin tests es un castillo de naipes**

### **🎯 MENTALIDAD TONY STARK**
- **Proactivo**: Testear antes de que los bugs aparezcan
- **Completo**: Cobertura total, no solo happy paths
- **Creativo**: Pensar como usuario malicioso, edge cases extremos
- **Eficiente**: Tests que fallen rápido y den información clara
- **Mantenible**: Tests que evolucionan con el código

---

**🎉 ¡FELICITACIONES! HAS COMPLETADO LA IMPLEMENTACIÓN COMPLETA DE TESTS PARA PRODUCTOS.**

Ahora eres capaz de:
- ✅ Diseñar arquitecturas de test escalables
- ✅ Implementar testing completo (unitario, integración, stress)
- ✅ Validar seguridad multi-tenant y RBAC
- ✅ Manejar concurrencia y race conditions
- ✅ Crear fixtures avanzadas y mocking inteligente
- ✅ Escribir tests maintainables y legibles

**¡Has alcanzado el nivel de Tony Stark en testing de software! 🦸‍♂️✨**

