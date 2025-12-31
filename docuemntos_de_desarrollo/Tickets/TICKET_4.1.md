# **🎯 TICKET 4.1: CRUD Completo de Productos**

## **📋 Descripción General**

Implementar el módulo central de **Gestión de Productos** siguiendo la arquitectura profesional del proyecto (Repository + Service). Este módulo permitirá a las empresas gestionar su menú o inventario de productos de forma aislada, segura y escalable.

---

## **🏗️ Propuesta Arquitectónica**

Seguiremos el patrón de diseño implementado en los módulos anteriores:

1. **Modelo (SQLModel)**: Definición de la tabla con multi-tenancy y soft delete.
2. **Esquemas (Pydantic)**: Validación de entrada y formateo de salida.
3. **Repositorio**: Abstracción de acceso a datos heredando de **BaseRepository**.
4. **Servicio**: Lógica de negocio (validaciones, cálculos, integración).
5. **Router**: Endpoints FastAPI protegidos por RBAC.

---

## **📁 Cambios Propuestos**

### **1. Modelos y Base de Datos**

### **[NEW] product.py**

**Campos Principales**:

- `name`: str (Único por empresa).
- `description`: text.
- `price`: **Decimal** (Obligatorio para precisión financiera, NUMERIC en SQL).
- `stock`: **float/Decimal** (Opcional, predeterminado 0).
- `image_url`: str (URL de la imagen).
- `category_id`: int (FK a Categories).
- `company_id`: int (Multi-tenant).
- **is_active**: bool (Soft delete).
- `tax_rate`: **Decimal** (IVA/Impuestos, precisión exacta).

### **[MODIFY] init.py**

- Importar y registrar el modelo `Product`.

### **2. Repositorio y Servicio (Escalabilidad)**

### **[NEW] product_repository.py**

- Heredar de `BaseRepository[Product]`.
- Implementar **decremento atómico de stock** (Lógica SQL: `UPDATE products SET stock = stock - 1 WHERE id = ? AND stock > 0`) para evitar condiciones de carrera.
- Implementar métodos específicos si es necesario (ej: `get_by_category`).

### **[NEW] product_service.py**

- Lógica de negocio avanzada.
- **Validación Anti-Cross-Tenant**: Verificar mediante consulta directa que el `category_id` pertenece a la misma `company_id` que el producto, previniendo inyección de IDs de otros tenants.
- Validación de existencia de categoría antes de crear producto.
- Manejo de unicidad de nombre por empresa.
- **Placeholder para subida de imágenes**.

### **3. API e Integración**

### **[NEW] product.py**

- `ProductCreate`, `ProductUpdate`, `ProductRead`, `ProductResponse`.

### **[NEW] product.py**

- `GET /products`: Listar con filtros (categoría, estado).
- `POST /products`: Crear (Requiere `products.create`).
- `GET /products/{id}`: Detalle (Requiere `products.read`).
- `PUT /products/{id}`: Actualizar (Requiere `products.update`).
- `DELETE /products/{id}`: Soft delete (Requiere `products.delete`).

---

## **🔓 Seguridad (RBAC)**

Se aplicarán los siguientes permisos (ya definidos en el sistema de semillas):

- `products.read`: Ver lista y detalle.
- `products.create`: Crear nuevos productos.
- `products.update`: Editar información.
- `products.delete`: Eliminar (inactivar) productos.

---

## **✅ Plan de Verificación**

### **Pruebas Automatizadas**

- **Unitarias**: Validación de precio positivo y unicidad de nombre.
- **Integración**: Flujo completo de creación -> listado -> eliminación.
- concurrencia:  stress testing **`asyncio.gather`** para simular este "ataque" de usuarios.
- **Multi-tenant**: Asegurar que la Empresa A no vea productos de la Empresa B.

### **Pruebas en Postman**

1. Crear producto con token de `admin`.
2. Intentar crear producto con token de `delivery` (Debe dar 403).
3. Listar productos y verificar que el `category_id` coincida.
4. Validar soft delete (**is_active** cambia a false).