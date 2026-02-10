# 🗺️ Matriz de Interacción del Sistema (Navegación)

Este documento sirve como índice central para la documentación técnica de los flujos del sistema. Cada módulo tiene su propia documentación detallada.

## 📚 Módulos Documentados

| Módulo | Documento de Detalle | Descripción |
| :--- | :--- | :--- |
| **Orders** | [ORDER_FLOW.md](./modulos/orders/ORDER_FLOW.md) | Flujo de vida de pedidos, estados (`PENDING` -> `DELIVERED`), cancelaciones y roles. |
| **Inventory** | [INVENTORY_FLOW.md](./modulos/inventory/INVENTORY_FLOW.md) | Gestión de stock, ajustes manuales, recetas e impacto de ventas en inventario. |
| **Users** | [USER_RBAC_FLOW.md](./modulos/users/USER_RBAC_FLOW.md) | Autenticación JWT, RBAC, roles (`owner`, `admin`, `waiter`, `cook`) y permisos. |
| **Menu** | [MENU_FLOW.md](./modulos/menu/MENU_FLOW.md) | Catálogo de productos, categorías, bebidas y relación con stock. |

---

## 🔗 Interconexiones Clave

### 1. Órdenes -> Inventario
- Al **confirmar** una orden (o entregarla), se descuenta stock.
- Al **cancelar** una orden, se restaura stock (`reverse=True`).
- Ver detalle en: [Deducción Automática](./modulos/inventory/INVENTORY_FLOW.md#deducción-automática-por-ventas)

### 2. Usuarios -> Órdenes
- Solo roles específicos pueden cambiar ciertos estados.
- Cancelaciones requieren permisos elevados o aprobación.
- Ver detalle en: [Matriz de Transiciones](./modulos/orders/ORDER_FLOW.md#matriz-de-transiciones-de-estado)

### 3. Reportes (Futuro)
- Los reportes agregan datos de Órdenes e Inventario.
- Acceso restringido a `admin` y `manager`.

---

> **Nota:** Esta documentación debe actualizarse si se agregan nuevos módulos o cambian las reglas de negocio fundamentales.
