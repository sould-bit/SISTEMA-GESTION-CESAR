# 📋 Flujo de Órdenes (Modulo: Orders)

Este documento define la matriz de interacción, permisos y flujos de estado para el módulo de Pedidos.

## 🎭 Roles y Permisos (RBAC)

| Rol del Sistema | Alias (Código) | Nivel de Acceso | Acciones Clave |
| :--- | :--- | :--- | :--- |
| **Mesero** | `waiter`, `server` | Operativo (Piso) | Crear Pedido, Agregar Items, *Solicitar* Cancelación, Entregar Pedido. |
| **Cajero** | `cashier` | Operativo (Control) | Confirmar Pedido, *Aprobar* Cancelación, Gestionar Pagos. |
| **Cocina** | `cook`, `kitchen` | Operativo (Producción) | Ver KDS, Marcar Listo, *Aprobar* Cancelación. |
| **Gerente/Admin** | `manager`, `admin`, `owner` | Supervisión Total | Cancelación Directa/Forzada, Reabrir Pedidos, Ver Reportes. |

---

El ciclo de vida del pedido (`Order.status`) se rige por la siguiente máquina de estados. 

> **Implementación Frontend:** Se utiliza una máquina de estados de **XState** (`order.machine.ts`) para gestionar estas transiciones en la UI, asegurando que solo se permitan acciones válidas según el estado actual y los permisos del usuario. Ver skill: `xstate_model_driven_dev`.


| Estado Actual | Transición (Acción) | Nuevo Estado | Roles Autorizados | API / Método Backend |
| :--- | :--- | :--- | :--- | :--- |
| `PENDING` | **Confirmar / Enviar a Cocina** | `PREPARING` | `cashier`, `manager`, `admin` | `POST /orders/{id}/status` |
| `PREPARING` | **Marcar como Listo** | `READY` | `kitchen`, `cashier`, `manager`, `admin` | `POST /orders/{id}/status` |
| `READY` | **Entregar a Mesa** | `DELIVERED` | `waiter`, `server`, `admin` | `POST /orders/{id}/status` |
| `ANY` | **Anular / Cancelar** | `CANCELLED` | *Ver Flujo de Cancelación* | `POST /orders/{id}/cancel` |

---

## 🛑 Flujo de Cancelación y Retornos

El sistema maneja las cancelaciones de manera jerárquica para proteger el inventario y evitar fraudes.

### 1. Cancelación Directa
**Condición:** El pedido está en estado `PENDING` **O** el usuario es `manager`/`admin`.
- **Acción:** El pedido pasa inmediatamente a `CANCELLED`.
- **Inventario:** Se revierte el consumo de stock automáticamente.

### 2. Solicitud de Cancelación (Veto)
**Condición:** El pedido está en `PREPARING` y el usuario es `waiter`.
- **Acción:**
    1. Mesero solicita cancelación con motivo.
    2. Estado del pedido no cambia, pero `cancellation_status` pasa a `pending`.
    3. **Alerta en KDS/Caja:** Aparece notificación de solicitud.
- **Resolución:**
    - **Aprobar:** (`cashier`, `kitchen`, `admin`) -> Pedido pasa a `CANCELLED`. Stock retornado.
    - **Denegar:** (`cashier`, `kitchen`, `admin`) -> Pedido se mantiene en `PREPARING`. `cancellation_status` pasa a `denied`.

---

## 📱 Mapa de Pantallas e Interacciones UI

| Pantalla / Componente | Acción UI | Rol Requerido | Endpoint |
| :--- | :--- | :--- | :--- |
| **POS (Toma de Orden)** | Botón "Enviar a Cocina" | `waiter` | `POST /orders` |
| **KDS (Cocina)** | Card > "Listo" | `kitchen` | `PUT /orders/{id}/status` |
| **KDS (Cocina)** | Alerta > "Aprobar Cancelación" | `kitchen` | `POST /orders/{id}/cancel-approval` |
| **Panel Caja** | Lista > "Confirmar Pago" | `cashier` | `POST /payments` |
| **Detalle Orden** | Botón "Solicitar Cancelación" | `waiter` | `POST /orders/{id}/cancel-request` |

---

## 🛠️ Especificaciones Técnicas

### Modelo de Datos Relacionado
- `Order.status`: Enum (`PENDING`, `PREPARING`, `READY`, `DELIVERED`, `CANCELLED`)
- `Order.cancellation_status`: String (`pending`, `approved`, `denied`, `none`)
- `Order.cancellation_requested_by`: FK `User.id`

### Servicios Implicados
- `OrderService`: Orquestador principal.
- `OrderStateMachine`: Validador de transiciones.
- `InventoryService`: Maneja el retorno de stock (`reverse=True`).
- `NotificationService`: Emite eventos WebSocket (`order:cancellation_requested`).
