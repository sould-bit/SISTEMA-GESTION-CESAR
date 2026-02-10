# 🍽️ Flujo de Menú y Productos (Modulo: Menu)

Este documento define la gestión del catálogo de productos, categorías y su relación con el inventario.

## 🎭 Roles y Permisos (RBAC)

| Rol del Sistema | Alias (Código) | Nivel de Acceso | Acciones Clave |
| :--- | :--- | :--- | :--- |
| **Admin/Gerente** | `admin`, `manager`, `owner` | Control Total | Crear/Editar Productos, Gestionar Categorías, Definir Precios. |
| **Cocina/Mesero** | `cook`, `waiter`, `cashier` | Lectura | Consultar menú para operar (POS/KDS). |

---

## 📦 Tipos de Productos y Flujos

### 1. Producto Estándar (Plato Elaborado)
**Endpoint:** `POST /products/`
- **Descripción:** Un item de venta que se compone de una Receta.
- **Relación Stock:**
    - Al venderse, descuenta stock de sus *Ingredientes* según la *Receta*.
    - No tiene stock directo en `Inventory` (su stock es virtual/calculado).

### 2. Bebida / Mercadería (Item Simple)
**Endpoint:** `POST /products/beverage`
- **Descripción:** Un producto que se compra y se vende tal cual (ej. Coca Cola, Cerveza).
- **Patrón "Puente 1:1":**
    - Se crea un `Product` (Venta).
    - Se crea un `Ingredient` (Stock).
    - Se crea una `Recipe` automática que vincula 1 a 1.
- **Relación Stock:**
    - Al venderse, descuenta 1 unidad del Ingrediente asociado.

---

## 📂 Categorización (Multi-Tenant)
**Endpoint:** `GET /categories/`
- Las categorías aíslan los productos lógicamente.
- **Multi-tenant:** Cada `Category` pertenece a una `company_id`. Un usuario solo ve categorías de su empresa.

---

## 📉 Visualización de Stock en Menú
**Endpoint:** `GET /products/inventory/low-stock`
- Permite identificar qué productos del menú están en riesgo de agotarse (basado en items tipo Bebida o cálculo de ingredientes críticos).

---

## 📱 Mapa de Pantallas e Interacciones UI

| Pantalla / Componente | Acción UI | Rol Requerido | Endpoint |
| :--- | :--- | :--- | :--- |
| **Gestión Menú** | Crear Producto | `admin`, `manager` | `POST /products` |
| **Gestión Menú** | Crear Bebida Rápida | `admin`, `manager` | `POST /products/beverage` |
| **POS** | Ver Menú Filtrado | `waiter`, `cashier` | `GET /products?category_id=...` |
