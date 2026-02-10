# 📦 Flujo de Inventario (Modulo: Inventory)

Este documento define la gestión de stock, ingredientes y ajustes de inventario.

## 🎭 Roles y Permisos (RBAC)

| Rol del Sistema | Alias (Código) | Nivel de Acceso | Acciones Clave |
| :--- | :--- | :--- | :--- |
| **Admin/Gerente** | `admin`, `manager`, `owner` | Control Total | Ajuste Manual, Creación de Ingredientes, Auditoría, Gestión de Costos. |
| **Cocina (Chef)** | `cook`, `chef` | Operativo (Limitado) | Ver Stock, Reportar Merma (Ajuste Negativo), Ver Recetas. |
| **Mesero/Cajero** | `waiter`, `cashier` | Lectura | Ver disponibilidad de productos (Indirectamente vía POS). |

---

## 🔄 Flujos de Gestión de Stock

### 1. Ajuste Manual de Stock (Inventario Físico)
**Endpoint:** `POST /inventory/adjust` o `POST /ingredients/{id}/stock`
**Roles:** `admin`, `manager`
- **Tipos de Transacción:**
    - `IN`: Entrada (Compra, Regalo).
    - `OUT`: Salida (Merma, Uso interno, Error).
    - `ADJ`: Ajuste por conteo físico (Set absolute value).
- **Impacto:** Actualiza `Inventory.stock` y crea registro en `InventoryTransaction`.

### 2. Gestión de Ingredientes y Costos
**Endpoint:** `POST /ingredients` / `PATCH /ingredients/{id}`
**Roles:** `admin`, `manager`
- **Flujo de Costo:**
    - Al recibir una compra (`POST /ingredients/{id}/update-cost`), se puede actualizar el costo.
    - **Trigger Automático:** El sistema recalcula el costo de todas las Recetas (`Recipe`) que usan este ingrediente.

### 3. Visualización y Alertas
**Endpoint:** `GET /inventory/{branch_id}` / `GET /inventory/alerts/{branch_id}`
**Roles:** `admin`, `manager`, `cook`
- **Alertas:** Se generan cuando `stock < min_stock`.
- **Uso:** El panel de cocina o administración muestra estos items en rojo.

---

## 📉 Deducción Automática por Ventas

El inventario se descuenta automáticamente al confirmar ventas en el módulo de Órdenes (`ORDER_FLOW.md`).

| Origen | Acción | Impacto en Inventario | Servicio |
| :--- | :--- | :--- | :--- |
| **Venta Producto** | `Order Created` | Reduce stock del Producto (si no tiene receta) | `InventoryService.update_stock` |
| **Venta Receta** | `Order Created` | Reduce stock de los Ingredientes componentes | `InventoryService.update_ingredient_stock` |
| **Modificador** | `Order Created` | Reduce stock del Modificador (Producto o Ingrediente) | `InventoryService.update_ingredient_stock` |
| **Cancelación** | `Order Cancelled` | Aumenta (Devuelve) stock al inventario (`reverse=True`) | `InventoryService` |

---

## 📱 Mapa de Pantallas e Interacciones UI

| Pantalla / Componente | Acción UI | Rol Requerido | Endpoint |
| :--- | :--- | :--- | :--- |
| **Panel Inventario** | Tabla de Insumos | `admin`, `manager` | `GET /ingredients` |
| **Panel Inventario** | Botón "Ajustar Stock" | `admin`, `manager` | `POST /ingredients/{id}/stock` |
| **Panel Recetas** | Editar Receta | `admin`, `manager` | `PATCH /recipes/{id}` |
| **Vista KDS/Stock** | Ver Alertas Stock Bajo | `cook`, `manager` | `GET /inventory/alerts` |
