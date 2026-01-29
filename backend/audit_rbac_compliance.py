import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.database import get_session
from app.models import User, Role, Permission
from app.services.permission_service import PermissionService
from app.core.rbac_defaults import DEFAULT_ROLE_PERMISSIONS_MAP, DEFAULT_PERMISSIONS

# Helper to expand wildcards (e.g. "orders.*" -> ["orders.create", "orders.read", ...])
def expand_permissions(short_codes):
    all_perms = [p["code"] for p in DEFAULT_PERMISSIONS]
    expanded = set()
    for code in short_codes:
        if code.endswith(".*"):
            prefix = code.split(".")[0]
            for p in all_perms:
                if p.startswith(prefix):
                    expanded.add(p)
        else:
            expanded.add(code)
    return expanded

from sqlalchemy.orm import selectinload

async def audit_rbac():
    # Manual session management
    session_gen = get_session()
    session = await anext(session_gen)

    try:
        print("\n🔐 AUDITORÍA DE CUMPLIMIENTO RBAC")
        print("===================================\n")

        # 1. Fetch Users
        # Eager load user_role to prevent MissingGreenlet
        result = await session.execute(
            select(User)
            .where(User.is_active == True)
            .options(selectinload(User.user_role))
        )
        users = result.scalars().all()
        
        perm_service = PermissionService(session)

        # 2. Iterate and Check
        for user in users:
            # Skip super-admin logic (users with role="admin" legacy or role_code="admin")
            # Although checking them is fine, they usually have "everything".
            
            print(f"👤 USUARIO: {user.username} (ID: {user.id})")
            
            # Determine Role
            role_code = "N/A"
            if user.role == "admin":
                 role_code = "admin"
            elif user.user_role:
                 role_code = user.user_role.code
            
            print(f"   Rol Detectado: {role_code}")
            
            if role_code == "admin":
                print("   ✅ ADMIN (Acceso Total Asumido)\n")
                continue

            # Get Actual Permissions from DB checks
            actual_perms = await perm_service.get_user_permission_codes(user.id, user.company_id)
            actual_set = set(actual_perms)

            # Get Expected Permissions from Defaults
            expected_short = DEFAULT_ROLE_PERMISSIONS_MAP.get(role_code, [])
            expected_set = expand_permissions(expected_short)

            if not expected_set and role_code not in ["admin"]:
                 print(f"   ⚠️ Rol '{role_code}' no tiene definición estándar en rbac_defaults.py")
            
            # Compare
            missing = expected_set - actual_set
            extra = actual_set - expected_set # Extra isn't necessarily bad, but good to know
            
            # Print Report
            if not missing and not extra:
                 print("   ✅ 100% CUMPLIMIENTO (Sincronizado con estándar)")
            else:
                 if missing:
                     print(f"   ❌ FALTAN PERMISOS (Crítico):")
                     for p in missing:
                         print(f"      - {p}")
                 
                 if extra:
                     print(f"   ℹ️  PERMISOS EXTRA (Personalizados):")
                     for p in extra:
                         print(f"      + {p}")
            
            print("")

            # TEST DE ACCESO REAL (Simulación)
            # Pick a few sample critical actions
            test_cases = [
                ("users.delete", "Eliminar Usuarios"),
                ("orders.create", "Crear Pedidos"),
                ("inventory.adjust", "Ajustar Inventario")
            ]

            print("   🔍 PRUEBA DE FUEGO (Acceso Real):")
            for perm_code, desc in test_cases:
                has_perm = perm_code in actual_set
                should_have = perm_code in expected_set
                
                status_icon = "✅" if has_perm == should_have else "❌"
                access_str = "PERMITIDO" if has_perm else "DENEGADO"
                
                print(f"      {status_icon} {desc} ({perm_code}): {access_str}")
            
            print("-" * 40)

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(audit_rbac())
