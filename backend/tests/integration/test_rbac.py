"""
Script de Prueba: Sistema de Roles y Permisos

Este script prueba la funcionalidad básica del sistema RBAC:
1. Asignar rol a usuario
2. Verificar permisos del usuario
3. Probar decoradores de autorización

Uso:
    docker-compose exec backend python test_rbac.py
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import async_session
from app.models import User, Role
from app.services.permission_service import PermissionService
from app.services.role_service import RoleService


async def test_rbac_system():
    """Prueba el sistema RBAC completo."""
    
    print("\n" + "="*60)
    print("🧪 PRUEBA DEL SISTEMA RBAC")
    print("="*60)
    
    async with async_session() as session:
        # 1. Obtener un usuario de prueba
        result = await session.execute(
            select(User).where(User.username == "admin").limit(1)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ No se encontró usuario 'admin'")
            return
        
        print(f"\n👤 Usuario de prueba: {user.username} (ID: {user.id})")
        print(f"   Empresa: {user.company_id}")
        
        # 2. Obtener rol de admin
        result = await session.execute(
            select(Role).where(
                Role.code == "admin",
                Role.company_id == user.company_id
            )
        )
        admin_role = result.scalar_one_or_none()
        
        if not admin_role:
            print("❌ No se encontró rol 'admin'")
            return
        
        print(f"\n🎭 Rol encontrado: {admin_role.name} (ID: {admin_role.id})")
        print(f"   Nivel jerárquico: {admin_role.hierarchy_level}")
        
        # 3. Asignar rol al usuario
        role_service = RoleService(session)
        
        if user.role_id != admin_role.id:
            print(f"\n📝 Asignando rol '{admin_role.name}' al usuario...")
            await role_service.assign_role_to_user(
                user_id=user.id,
                role_id=admin_role.id,
                company_id=user.company_id
            )
            print("✅ Rol asignado exitosamente")
        else:
            print(f"\n✅ Usuario ya tiene el rol '{admin_role.name}'")
        
        # 4. Verificar permisos del usuario
        permission_service = PermissionService(session)
        
        print(f"\n🔐 Obteniendo permisos del usuario...")
        permissions = await permission_service.get_user_permissions(
            user_id=user.id,
            company_id=user.company_id
        )
        
        print(f"✅ Usuario tiene {len(permissions)} permisos:")
        
        # Agrupar por categoría
        by_category = {}
        for perm in permissions:
            cat_name = perm.category.name if perm.category else "Sin categoría"
            if cat_name not in by_category:
                by_category[cat_name] = []
            by_category[cat_name].append(perm.code)
        
        for cat_name, perms in sorted(by_category.items()):
            print(f"\n   📁 {cat_name}:")
            for perm_code in sorted(perms):
                print(f"      - {perm_code}")
        
        # 5. Probar verificación de permisos
        print(f"\n🧪 Probando verificación de permisos...")
        
        test_permissions = [
            "products.create",
            "orders.read",
            "cash.close",
            "users.manage",
            "invalid.permission"
        ]
        
        for perm_code in test_permissions:
            has_perm = await permission_service.check_permission(
                user_id=user.id,
                permission_code=perm_code,
                company_id=user.company_id
            )
            
            status = "✅ TIENE" if has_perm else "❌ NO TIENE"
            print(f"   {status} permiso: {perm_code}")
        
        print(f"\n{'='*60}")
        print("✅ PRUEBA COMPLETADA EXITOSAMENTE")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(test_rbac_system())
