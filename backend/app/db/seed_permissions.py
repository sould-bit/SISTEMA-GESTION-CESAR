"""
Seed de Datos Iniciales: Sistema de Permisos y Roles (RBAC)

Este script crea:
1. Categorías de permisos del sistema
2. Permisos granulares por recurso y acción
3. Roles predefinidos con jerarquía
4. Asignación de permisos a roles

Uso:
    docker-compose exec backend python -m app.db.seed_permissions
"""

import asyncio
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import async_session
from app.models import (
    PermissionCategory,
    Permission,
    Role,
    RolePermission,
    Company
)


# ============================================================================
# CATEGORÍAS DEL SISTEMA
# ============================================================================
SYSTEM_CATEGORIES = [
    {
        "code": "core",
        "name": "Core",
        "description": "Funcionalidades core del sistema",
        "icon": "settings",
        "color": "#607D8B"
    },
    {
        "code": "products",
        "name": "Productos",
        "description": "Gestión de productos y menú",
        "icon": "restaurant",
        "color": "#FF9800"
    },
    {
        "code": "orders",
        "name": "Pedidos",
        "description": "Gestión de pedidos y ventas",
        "icon": "receipt_long",
        "color": "#4CAF50"
    },
    {
        "code": "inventory",
        "name": "Inventario",
        "description": "Control de inventario y stock",
        "icon": "inventory_2",
        "color": "#2196F3"
    },
    {
        "code": "finance",
        "name": "Finanzas",
        "description": "Gestión financiera y caja",
        "icon": "account_balance",
        "color": "#9C27B0"
    },
    {
        "code": "reports",
        "name": "Reportes",
        "description": "Reportes y analytics",
        "icon": "analytics",
        "color": "#00BCD4"
    },
    {
        "code": "admin",
        "name": "Administración",
        "description": "Administración del sistema",
        "icon": "admin_panel_settings",
        "color": "#F44336"
    }
]


# ============================================================================
# PERMISOS DEL SISTEMA
# ============================================================================
SYSTEM_PERMISSIONS = [
    # === CORE ===
    {"category": "core", "resource": "dashboard", "action": "view", "name": "Ver Dashboard"},
    {"category": "core", "resource": "settings", "action": "read", "name": "Ver Configuración"},
    {"category": "core", "resource": "settings", "action": "update", "name": "Modificar Configuración"},
    
    # === PRODUCTOS ===
    {"category": "products", "resource": "products", "action": "create", "name": "Crear Productos"},
    {"category": "products", "resource": "products", "action": "read", "name": "Ver Productos"},
    {"category": "products", "resource": "products", "action": "update", "name": "Modificar Productos"},
    {"category": "products", "resource": "products", "action": "delete", "name": "Eliminar Productos"},
    {"category": "products", "resource": "categories", "action": "manage", "name": "Gestionar Categorías"},
    {"category": "products", "resource": "recipes", "action": "manage", "name": "Gestionar Recetas"},
    
    # === PEDIDOS ===
    {"category": "orders", "resource": "orders", "action": "create", "name": "Crear Pedidos"},
    {"category": "orders", "resource": "orders", "action": "read", "name": "Ver Pedidos"},
    {"category": "orders", "resource": "orders", "action": "update", "name": "Gestionar Estados (Aceptar/Entregar)"},
    {"category": "orders", "resource": "orders", "action": "cancel", "name": "Cancelar Pedidos"},
    {"category": "orders", "resource": "orders", "action": "manage_all", "name": "Gestionar Todos los Pedidos"},
    {"category": "orders", "resource": "kitchen", "action": "view", "name": "Ver Pedidos de Cocina"},
    {"category": "orders", "resource": "kitchen", "action": "update_status", "name": "Actualizar Estado de Cocina"},
    
    # === INVENTARIO ===
    {"category": "inventory", "resource": "inventory", "action": "read", "name": "Ver Inventario"},
    {"category": "inventory", "resource": "inventory", "action": "adjust", "name": "Ajustar Inventario"},
    {"category": "inventory", "resource": "inventory", "action": "transfer", "name": "Transferir Inventario"},
    {"category": "inventory", "resource": "suppliers", "action": "manage", "name": "Gestionar Proveedores"},
    
    # === FINANZAS ===
    {"category": "finance", "resource": "cash", "action": "open", "name": "Abrir Caja"},
    {"category": "finance", "resource": "cash", "action": "close", "name": "Cerrar Caja"},
    {"category": "finance", "resource": "cash", "action": "view_balance", "name": "Ver Balance de Caja"},
    {"category": "finance", "resource": "payments", "action": "process", "name": "Procesar Pagos"},
    {"category": "finance", "resource": "payments", "action": "refund", "name": "Reembolsar Pagos"},
    
    # === REPORTES ===
    {"category": "reports", "resource": "reports", "action": "sales", "name": "Ver Reportes de Ventas"},
    {"category": "reports", "resource": "reports", "action": "inventory", "name": "Ver Reportes de Inventario"},
    {"category": "reports", "resource": "reports", "action": "financial", "name": "Ver Reportes Financieros"},
    {"category": "reports", "resource": "reports", "action": "export", "name": "Exportar Reportes"},
    
    # === ADMINISTRACIÓN ===
    {"category": "admin", "resource": "users", "action": "create", "name": "Crear Usuarios"},
    {"category": "admin", "resource": "users", "action": "read", "name": "Ver Usuarios"},
    {"category": "admin", "resource": "users", "action": "update", "name": "Modificar Usuarios"},
    {"category": "admin", "resource": "users", "action": "delete", "name": "Eliminar Usuarios"},
    {"category": "admin", "resource": "roles", "action": "manage", "name": "Gestionar Roles"},
    {"category": "admin", "resource": "permissions", "action": "manage", "name": "Gestionar Permisos"},
    {"category": "admin", "resource": "branches", "action": "manage", "name": "Gestionar Sucursales"},
]


# ============================================================================
# ROLES DEL SISTEMA
# ============================================================================
SYSTEM_ROLES = [
    {
        "code": "super_admin",
        "name": "Super Administrador",
        "description": "Acceso total al sistema. Control completo de configuración y usuarios.",
        "hierarchy_level": 100,
        "permissions": "ALL"  # Tendrá todos los permisos
    },
    {
        "code": "admin",
        "name": "Administrador",
        "description": "Gestión completa excepto configuración crítica del sistema.",
        "hierarchy_level": 80,
        "permissions": [
            # Core
            "dashboard.view", "settings.read",
            # Productos
            "products.create", "products.read", "products.update", "products.delete",
            "categories.manage", "recipes.manage",
            # Pedidos
            "orders.create", "orders.read", "orders.update", "orders.cancel", "orders.manage_all",
            # Inventario
            "inventory.read", "inventory.adjust", "inventory.transfer", "suppliers.manage",
            # Finanzas
            "cash.open", "cash.close", "cash.view_balance", "payments.process", "payments.refund",
            # Reportes
            "reports.sales", "reports.inventory", "reports.financial", "reports.export",
            # Admin
            "users.create", "users.read", "users.update", "branches.manage"
        ]
    },
    {
        "code": "manager",
        "name": "Gerente",
        "description": "Supervisión de operaciones y acceso a reportes.",
        "hierarchy_level": 60,
        "permissions": [
            "dashboard.view", "settings.read",
            "products.read", "categories.manage",
            "orders.create", "orders.read", "orders.update", "orders.cancel", "orders.manage_all",
            "inventory.read", "inventory.adjust",
            "cash.view_balance", "payments.process",
            "reports.sales", "reports.inventory", "reports.financial",
            "users.read"
        ]
    },
    {
        "code": "cashier",
        "name": "Cajero",
        "description": "Ventas, caja y pedidos básicos.",
        "hierarchy_level": 40,
        "permissions": [
            "dashboard.view",
            "products.read",
            "orders.create", "orders.read", "orders.update", "orders.cancel",
            "cash.open", "cash.close", "cash.view_balance",
            "payments.process"
        ]
    },
    {
        "code": "kitchen",
        "name": "Cocina",
        "description": "Gestión de pedidos de cocina únicamente.",
        "hierarchy_level": 30,
        "permissions": [
            "kitchen.view", "kitchen.update_status",
            "orders.read"
        ]
    },
    {
        "code": "delivery",
        "name": "Domiciliario",
        "description": "Visualización y actualización de pedidos de domicilio.",
        "hierarchy_level": 20,
        "permissions": [
            "orders.read", "orders.update"
        ]
    },
    {
        "code": "viewer",
        "name": "Visualizador",
        "description": "Solo lectura de información básica.",
        "hierarchy_level": 10,
        "permissions": [
            "dashboard.view",
            "products.read",
            "orders.read"
        ]
    }
]


# ============================================================================
# FUNCIONES DE SEED
# ============================================================================

async def seed_permission_categories(session: AsyncSession, company_id: int) -> dict[str, UUID]:
    """
    Crea las categorías de permisos del sistema.
    Retorna un diccionario {code: id} para referencia.
    """
    print(f"\n📁 Creando categorías de permisos para company_id={company_id}...")
    
    category_map = {}
    
    for cat_data in SYSTEM_CATEGORIES:
        stmt = select(PermissionCategory).where(
            PermissionCategory.company_id == company_id,
            PermissionCategory.code == cat_data["code"]
        )
        result = await session.execute(stmt)
        existing_cat = result.scalar_one_or_none()

        if existing_cat:
            existing_cat.name = cat_data["name"]
            existing_cat.description = cat_data["description"]
            existing_cat.icon = cat_data.get("icon")
            existing_cat.color = cat_data.get("color")
            category_map[cat_data["code"]] = existing_cat.id
            print(f"  🔄 {cat_data['name']} ({cat_data['code']}) (Actualizado)")
        else:
            category = PermissionCategory(
                id=uuid4(),
                company_id=company_id,
                code=cat_data["code"],
                name=cat_data["name"],
                description=cat_data["description"],
                icon=cat_data.get("icon"),
                color=cat_data.get("color"),
                is_system=True,
                is_active=True
            )
            session.add(category)
            category_map[cat_data["code"]] = category.id
            print(f"  ✅ {cat_data['name']} ({cat_data['code']}) (Creado)")
    
    await session.commit()
    return category_map


async def seed_permissions(
    session: AsyncSession,
    company_id: int,
    category_map: dict[str, UUID]
) -> dict[str, UUID]:
    """
    Crea los permisos del sistema.
    Retorna un diccionario {code: id} para referencia.
    """
    print(f"\n🔐 Creando permisos del sistema para company_id={company_id}...")
    
    permission_map = {}
    
    for perm_data in SYSTEM_PERMISSIONS:
        category_id = category_map[perm_data["category"]]
        code = f"{perm_data['resource']}.{perm_data['action']}"
        
        # Check if permission exists
        stmt = select(Permission).where(
            Permission.company_id == company_id,
            Permission.code == code
        )
        result = await session.execute(stmt)
        existing_perm = result.scalar_one_or_none()
        
        if existing_perm:
            # Update existing
            existing_perm.name = perm_data["name"]
            existing_perm.description = f"Permiso para {perm_data['name'].lower()}"
            existing_perm.category_id = category_id
            existing_perm.resource = perm_data["resource"]
            existing_perm.action = perm_data["action"]
            permission_map[code] = existing_perm.id
            print(f"  🔄 {code} - {perm_data['name']} (Actualizado)")
        else:
            # Create new
            permission = Permission(
                id=uuid4(),
                company_id=company_id,
                category_id=category_id,
                code=code,
                name=perm_data["name"],
                description=f"Permiso para {perm_data['name'].lower()}",
                resource=perm_data["resource"],
                action=perm_data["action"],
                is_system=True,
                is_active=True
            )
            session.add(permission)
            permission_map[code] = permission.id
            print(f"  ✅ {code} - {perm_data['name']} (Creado)")
    
    await session.commit()
    return permission_map


async def seed_roles(
    session: AsyncSession,
    company_id: int,
    permission_map: dict[str, UUID]
) -> dict[str, UUID]:
    """
    Crea los roles del sistema y asigna permisos.
    Retorna un diccionario {code: id} para referencia.
    """
    print(f"\n👥 Creando roles del sistema para company_id={company_id}...")
    
    role_map = {}
    
    for role_data in SYSTEM_ROLES:
        stmt = select(Role).where(
            Role.company_id == company_id,
            Role.code == role_data["code"]
        )
        result = await session.execute(stmt)
        existing_role = result.scalar_one_or_none()

        role_id = None
        
        if existing_role:
            existing_role.name = role_data["name"]
            existing_role.description = role_data["description"]
            existing_role.hierarchy_level = role_data["hierarchy_level"]
            role_id = existing_role.id
            role_map[role_data["code"]] = role_id
            print(f"  🔄 {role_data['name']} ({role_data['code']}) (Actualizado)")
        else:
            role = Role(
                id=uuid4(),
                company_id=company_id,
                code=role_data["code"],
                name=role_data["name"],
                description=role_data["description"],
                hierarchy_level=role_data["hierarchy_level"],
                is_system=True,
                is_active=True
            )
            session.add(role)
            role_id = role.id
            role_map[role_data["code"]] = role_id
            print(f"  ✅ {role_data['name']} ({role_data['code']}) (Creado)")
        
        # Asignar permisos al rol (Sync permissions)
        if role_data["permissions"] == "ALL":
            permissions_to_assign = list(permission_map.values())
        else:
            permissions_to_assign = [
                permission_map[perm_code]
                for perm_code in role_data["permissions"]
                if perm_code in permission_map
            ]
            
        # Clear existing role permissions first if simplistic approach, or merge?
        # Ideally we want to ensure role has exactly these permissions if it's a system role.
        # But user might have added custom permissions? 
        # Since these are SYSTEM_ROLES, we probably want to enforce system permissions.
        # But removing user-added permissions might be aggressive.
        
        # Let's just ensure the system permissions are added.
        # We need to know which ones are already assigned.
        
        stmt_rp = select(RolePermission.permission_id).where(RolePermission.role_id == role_id)
        result_rp = await session.execute(stmt_rp)
        current_perm_ids = set(result_rp.scalars().all())
        
        count_added = 0
        for perm_id in permissions_to_assign:
            if perm_id not in current_perm_ids:
                role_permission = RolePermission(
                    id=uuid4(),
                    role_id=role_id,
                    permission_id=perm_id,
                    granted_by=None
                )
                session.add(role_permission)
                count_added += 1
        
        print(f"    → {count_added} nuevos permisos asignados (Total sistema: {len(permissions_to_assign)})")
    
    await session.commit()
    return role_map


async def seed_permissions_for_company(company_id: int):
    """
    Ejecuta el seed completo de permisos para una empresa.
    """
    async with async_session() as session:
        print(f"\n{'='*60}")
        print(f"🚀 INICIANDO SEED DE PERMISOS PARA COMPANY_ID={company_id}")
        print(f"{'='*60}")
        
        # 1. Crear categorías
        category_map = await seed_permission_categories(session, company_id)
        
        # 2. Crear permisos
        permission_map = await seed_permissions(session, company_id, category_map)
        
        # 3. Crear roles y asignar permisos
        role_map = await seed_roles(session, company_id, permission_map)
        
        print(f"\n{'='*60}")
        print(f"✅ SEED COMPLETADO EXITOSAMENTE")
        print(f"{'='*60}")
        print(f"📊 Resumen:")
        print(f"  - Categorías creadas: {len(category_map)}")
        print(f"  - Permisos creados: {len(permission_map)}")
        print(f"  - Roles creados: {len(role_map)}")
        print(f"{'='*60}\n")


async def seed_all_companies():
    """
    Ejecuta el seed para todas las empresas existentes.
    """
    async with async_session() as session:
        # Obtener todas las empresas
        result = await session.execute(select(Company))
        companies = result.scalars().all()
        
        if not companies:
            print("⚠️  No hay empresas en la base de datos.")
            print("   Ejecuta primero el seed de empresas: python seed_simple.py")
            return
        
        print(f"\n🏢 Encontradas {len(companies)} empresas")
        
        for company in companies:
            await seed_permissions_for_company(company.id)


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Punto de entrada principal."""
    print("\n" + "="*60)
    print("🔐 SEED DE SISTEMA DE PERMISOS Y ROLES (RBAC)")
    print("="*60)
    
    await seed_all_companies()
    
    print("\n✅ Proceso completado. El sistema de permisos está listo.")
    print("💡 Ahora puedes asignar roles a usuarios existentes.\n")


if __name__ == "__main__":
    asyncio.run(main())
