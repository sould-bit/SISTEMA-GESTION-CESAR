# 👥 Gestión de Usuarios y Accesos (Modulo: Users)

Este documento define la autenticación, autorización y roles del sistema.

## 🔐 Autenticación y Seguridad

El sistema utiliza **JWT (JSON Web Tokens)** para seguridad sin estado (stateless).
- **Token**: `Authorization: Bearer <token>`
- **Expiración**: Configurable (default 24h).
- **Alcance**: Los tokens están vinculados a una `company_id` específica.

### Flujo de Login
1. `POST /auth/login` con credenciales.
2. Backend valida y devuelve `access_token`.
3. Frontend almacena token y lo envía en cada request.

---

## 🎭 Matriz de Roles y Permisos

Los roles definen qué puede hacer un usuario. Se gestionan dinámicamente pero existen defaults.

| Rol (Código) | Permisos Clave | Alcance |
| :--- | :--- | :--- |
| **Owner** | `*` (Superadmin de Empresa) | Acceso total a configuración, facturación y usuarios. |
| **Admin** | `users.*`, `inventory.*`, `orders.*`, `reports.*` | Gestión operativa completa. |
| **Manager** | `inventory.*`, `orders.*`, `reports.read` | Supervisión de turno y stock. |
| **Cashier** | `orders.create`, `orders.update`, `payments.*` | Caja, cobros y anulaciones leves. |
| **Waiter** | `orders.create`, `orders.read`, `tables.read` | Toma de pedidos limitada. |
| **Kitchen** | `orders.read`, `orders.update_status` | KDS (Pantalla de Cocina). |

### Permiso por Endpoint (Ejemplos)

| Endpoint | Permiso Requerido | Roles Típicos |
| :--- | :--- | :--- |
| `POST /users` | `users.create` | `owner`, `admin` |
| `DELETE /users/{id}` | `users.delete` | `owner` |
| `POST /inventory/adjust` | `inventory.adjust` | `admin`, `manager` |
| `POST /orders/{id}/cancel` | `orders.cancel` | `manager`, `admin`, `cashier`* |

*\*Cashier puede requerir aprobación según configuración.*

---

## 🔄 Ciclo de Vida del Usuario

1. **Alta**:
   - `Owner` se crea al registrar la empresa (`POST /auth/register`).
   - `Owner` crea empleados (`POST /users/`) asignando rol y sucursal.
2. **Actividad**:
   - Usuario activo puede loguearse y operar según rol.
3. **Baja (Soft Delete)**:
   - `DELETE /users/{id}` desactiva el acceso inmediatamente.
   - Datos históricos (órdenes creadas) se mantienen por integridad referencial.

---

## 📱 Mapa de Pantallas e Interacciones UI

| Pantalla / Componente | Acción UI | Rol Requerido | Endpoint |
| :--- | :--- | :--- | :--- |
| **Login** | Ingresar Credenciales | *Público* | `POST /auth/login` |
| **Registro Empresa** | Crear Cuenta | *Público* | `POST /auth/register` |
| **Gestión Usuarios** | Crear/Editar Empleado | `owner`, `admin` | `POST /users`, `PUT /users/{id}` |
| **Perfil** | Ver Mis Datos | *Auth* | `GET /auth/me` |
