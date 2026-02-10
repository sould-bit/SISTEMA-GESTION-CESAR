# 📊 Matriz de Interacción Técnica: Módulo de Pedidos

Esta matriz mapea los elementos visuales (Frontend) con la lógica de negocio y seguridad (Backend), sirviendo como la guía definitiva para el desarrollo y depuración del flujo de órdenes.

## 📋 Matriz de Acciones (Vista General)

| N° | Ubicación (Pantalla/Componente) | Elemento (UI Trigger) | Permisos/Roles (RBAC) | Servicio Backend (API/Función) | Impacto en Estado (DB) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **01** | `PWA Cliente` / `App Mesero` | Botón "Confirmar Pedido" | `waiter`, `server`, `customer` | `POST /orders/` | `INIT` ➔ `PENDING` |
| **02** | `Admin Panel` > `PendingOrders` | Botón "Preparar" (Check) | `cashier`, `manager`, `admin` | `order_service.confirm()` | `PENDING` ➔ `PREPARING` |
| **03** | `Kitchen Display System (KDS)` | Card "Marcar como Listo" | `cashier`, `manager`, `admin` | `order_service.set_ready()` | `PREPARING` ➔ `READY` |
| **04** | `Panel Operativo` > `OrderCard` | Botón "Entregar" | `waiter`, `server`, `admin` | `order_service.deliver()` | `READY` ➔ `DELIVERED` |
| **05** | `OrderDetailsModal` | Botón "Cancelar" (Simple) | **Todos** (Auth) | `order_service.cancel()` | `PENDING` ➔ `CANCELLED` |
| **06** | `Admin Settings` | Botón "Anular Pedido" (Crítica) | `manager`, `admin`, `owner` | `order_service.critical_cancel()` | `ANY` ➔ `CANCELLED` |

---

## 🛠️ Especificaciones Técnicas por Acción

### 1. Flujo de Cocina (Acciones 02 y 03)
- **Frontend:** Implementado en el panel administrativo y operativo.
- **Backend:** Valida que el `company_id` coincida y que el usuario tenga rol de gestión.
- **WebSocket:** Emite evento `order_status_update` para notificar al mesero.

### 2. Flujo de Entrega (Acción 04)
- **Frontend:** El botón solo es visible/habilitado si el estado es `READY`.
- **Backend:** Permite el alias `server` (rol de Valen) para completar la transición.
- **Auditoría:** Se registra el `waiter_id` que realizó la entrega física.

### 3. Sistema de Cancelaciones (Acciones 05 y 06)
- **Validación:**
    - Si el pedido está en `PREPARING`, se requiere confirmación de jefe de cocina/admin.
    - Si el pedido está en `DELIVERED`, la cancelación es bloqueada (requiere flujo de devolución).

---

## 💡 Cómo usar esta Matriz
1. **Para Frontend:** Úsala para decidir qué roles deben ver (renderizar) un botón específico usando el componente `<RequirePermission>`.
2. **Para Backend:** Úsala para verificar que el decorador `@require_permission` coincida con lo documentado aquí.
3. **Para QA/Testing:** Cada fila de esta matriz representa un caso de prueba (Test Case) que debe ser validado.
