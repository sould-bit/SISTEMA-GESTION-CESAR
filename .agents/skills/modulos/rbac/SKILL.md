---
name: rbac_state_machine
description: Reglas y parámetros del sistema de Control de Acceso basado en Roles (RBAC) aplicado a la Máquina de Estados de Pedidos.
---

# Skill: RBAC & State Machine (Módulo de Gestión de Pedidos)

Este skill documenta la lógica de autorización y transiciones permitidas en el ciclo de vida de los pedidos dentro de del sistema.

## 1. Mapeo de Roles y Alias
Para simplificar la lógica del backend y mantener compatibilidad con el frontend, los roles se agrupan en las siguientes categorías lógicas:

| Categoría Lógica | Alias de Roles Soportados | Responsabilidades Principales |
| :--- | :--- | :--- |
| **Servicio (Meseros)** | `waiter`, `server` | Atención en mesa, entrega de pedidos listos. |
| **Operación (Caja)** | `cashier`, `manager` | Aceptación de pedidos, gestión de preparación. |
| **Administración** | `admin`, `owner`, `super_admin` | Gestión total, cancelaciones críticas, reportes. |
| **Logística** | `delivery` | Solo entregas a domicilio. |

## 2. Grafo de Transiciones y Permisos (RBAC_RULES)

La Máquina de Estados valida que el usuario tenga el rol adecuado para cada cambio de estado específico.

### A. Gestión de Preparación y Aceptación
*Roles Permitidos:* `cashier`, `manager`, `admin`, `owner`, `super_admin`
- `PENDING` → `CONFIRMED` / `PREPARING`
- `CONFIRMED` → `PREPARING`
- `PREPARING` → `READY`
*Restricción:* Los meseros (`server`/`waiter`) **no** pueden iniciar la preparación ni marcar como listo.

### B. Gestión de Entrega
*Roles Permitidos:* `waiter`, `server`, `delivery`, `admin`, `owner`, `super_admin`
- `READY` → `DELIVERED`
*Restricción:* Los cajeros y personal operativo base **no** pueden marcar pedidos como entregados.

### C. Sistema de Cancelaciones
1. **Cancelación Simple**:
   - `PENDING` → `CANCELLED`
   - *Permiso:* Todos los roles autorizados.
2. **Cancelación Crítica** (Pedidos ya en proceso o terminados):
   - `CONFIRMED` / `PREPARING` / `READY` → `CANCELLED`
   - *Permiso:* Solo Jefes y Administradores (`manager`, `admin`, `owner`, `super_admin`).

## 3. Implementación Técnica
Las reglas residen en `backend/app/services/order_state_machine.py` bajo el diccionario `RBAC_RULES`.
- Se utiliza el método `transition()` para validar tanto el grafo de estados como los permisos del usuario.
- El sistema es case-insensitive para los códigos de rol.

## 4. Mejores Prácticas
- Al agregar un nuevo rol en el futuro, verificar en qué categoría lógica encaja (Servicio, Operación o Admin).
- Si un usuario recibe un error `403`, verificar si su código de rol está incluido en el conjunto (Set) de la transición correspondiente en `RBAC_RULES`.
