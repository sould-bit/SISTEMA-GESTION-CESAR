"""
🔐 RBAC DEFAULTS - Configuración predeterminada de Roles y Permisos

Fuente única de verdad para la configuración inicla de RBAC.
Se usa en:
1. Registro de nuevas empresas (RegistrationService)
2. Seeding de roles (RoleSeeder)
3. Scripts de migración y reparación
"""

# Categorías de permisos
DEFAULT_PERMISSION_CATEGORIES = [
    {"code": "products", "name": "Productos", "icon": "inventory_2", "color": "#4CAF50"},
    {"code": "orders", "name": "Pedidos", "icon": "receipt_long", "color": "#2196F3"},
    {"code": "inventory", "name": "Inventario", "icon": "warehouse", "color": "#FF9800"},
    {"code": "cash", "name": "Caja", "icon": "point_of_sale", "color": "#9C27B0"},
    {"code": "reports", "name": "Reportes", "icon": "analytics", "color": "#607D8B"},
    {"code": "users", "name": "Usuarios", "icon": "people", "color": "#F44336"},
    {"code": "settings", "name": "Configuración", "icon": "settings", "color": "#795548"},
    {"code": "admin", "name": "Administración", "icon": "admin_panel_settings", "color": "#673AB7"},
]

# Lista plana de permisos
DEFAULT_PERMISSIONS = [
    # Productos
    {"category": "products", "code": "products.create", "name": "Crear productos", "resource": "products", "action": "create"},
    {"category": "products", "code": "products.read", "name": "Ver productos", "resource": "products", "action": "read"},
    {"category": "products", "code": "products.update", "name": "Editar productos", "resource": "products", "action": "update"},
    {"category": "products", "code": "products.delete", "name": "Eliminar productos", "resource": "products", "action": "delete"},
    # Pedidos
    {"category": "orders", "code": "orders.create", "name": "Crear pedidos", "resource": "orders", "action": "create"},
    {"category": "orders", "code": "orders.read", "name": "Ver pedidos", "resource": "orders", "action": "read"},
    {"category": "orders", "code": "orders.update", "name": "Actualizar pedidos", "resource": "orders", "action": "update"},
    {"category": "orders", "code": "orders.cancel", "name": "Cancelar pedidos", "resource": "orders", "action": "cancel"},
    # Inventario
    {"category": "inventory", "code": "inventory.read", "name": "Ver inventario", "resource": "inventory", "action": "read"},
    {"category": "inventory", "code": "inventory.adjust", "name": "Ajustar inventario", "resource": "inventory", "action": "adjust"},
    # Caja
    {"category": "cash", "code": "cash.open", "name": "Abrir caja", "resource": "cash", "action": "open"},
    {"category": "cash", "code": "cash.close", "name": "Cerrar caja", "resource": "cash", "action": "close"},
    {"category": "cash", "code": "cash.read", "name": "Ver movimientos", "resource": "cash", "action": "read"},
    # Reportes
    {"category": "reports", "code": "reports.sales", "name": "Ver reportes de ventas", "resource": "reports", "action": "sales"},
    {"category": "reports", "code": "reports.financial", "name": "Ver reportes financieros", "resource": "reports", "action": "financial"},
    # Usuarios
    {"category": "users", "code": "users.create", "name": "Crear usuarios", "resource": "users", "action": "create"},
    {"category": "users", "code": "users.read", "name": "Ver usuarios", "resource": "users", "action": "read"},
    {"category": "users", "code": "users.update", "name": "Editar usuarios", "resource": "users", "action": "update"},
    {"category": "users", "code": "users.delete", "name": "Eliminar usuarios", "resource": "users", "action": "delete"},
    # Configuración
    {"category": "settings", "code": "settings.read", "name": "Ver configuración", "resource": "settings", "action": "read"},
    {"category": "settings", "code": "settings.update", "name": "Modificar configuración", "resource": "settings", "action": "update"},
    # Admin RBAC
    {"category": "admin", "code": "roles.create", "name": "Crear roles", "resource": "roles", "action": "create"},
    {"category": "admin", "code": "roles.read", "name": "Ver roles", "resource": "roles", "action": "read"},
    {"category": "admin", "code": "roles.update", "name": "Editar roles", "resource": "roles", "action": "update"},
    {"category": "admin", "code": "roles.delete", "name": "Eliminar roles", "resource": "roles", "action": "delete"},
    {"category": "admin", "code": "permissions.read", "name": "Ver permisos", "resource": "permissions", "action": "read"},
    {"category": "admin", "code": "permissions.update", "name": "Asignar permisos", "resource": "permissions", "action": "update"},
    {"category": "admin", "code": "categories.read", "name": "Ver categorías", "resource": "categories", "action": "read"},
    {"category": "admin", "code": "categories.create", "name": "Crear categorías", "resource": "categories", "action": "create"},
]

# Roles Operativos Predeterminados
DEFAULT_OPERATIONAL_ROLES = [
    {
        "name": "Gerente",
        "code": "manager",
        "description": "Gestión operativa del negocio",
        "hierarchy": 90
    },
    {
        "name": "Cajero",
        "code": "cashier",
        "description": "Manejo de caja y cobros",
        "hierarchy": 50
    },
    {
        "name": "Cocinero",
        "code": "cook",
        "description": "Pantalla de cocina e inventario",
        "hierarchy": 40
    },
    {
        "name": "Mesero",
        "code": "server",
        "description": "Toma de pedidos y atención",
        "hierarchy": 30
    },
    {
        "name": "Repartidor",
        "code": "delivery",
        "description": "Entrega de pedidos",
        "hierarchy": 20
    }
]

# Mapa de Permisos por Defecto para Roles
DEFAULT_ROLE_PERMISSIONS_MAP = {
    "manager": [
        "products.*", "orders.*", "inventory.*", "cash.*", "reports.*", "users.read"
    ],
    "cashier": [
        "orders.*", "cash.*", "products.read", "reports.sales"
    ],
    "server": [
        "orders.create", "orders.read", "orders.update", "products.read"
    ],
    "cook": [
        "orders.read", "orders.update", "inventory.read", "inventory.adjust"
    ],
    "delivery": [
        "orders.read", "orders.update"
    ]
}
