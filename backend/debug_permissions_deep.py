
import asyncio
from sqlalchemy import select
from app.database import async_session
from app.models import User, Role, RolePermission, Permission

async def deep_inspect():
    async with async_session() as session:
        print("\n=== USERS DIAGNOSTIC ===")
        stmt = select(User)
        users = (await session.execute(stmt)).scalars().all()
        
        for u in users:
            print(f"\nUser: {u.username} (ID: {u.id}) | Company: {u.company_id} | RoleID: {u.role_id}")
            if not u.role_id:
                print("  [ERROR] No Role ID assigned!")
                continue
                
            # Check Role
            role_stmt = select(Role).where(Role.id == u.role_id)
            role = (await session.execute(role_stmt)).scalar_one_or_none()
            if not role:
                 print("  [ERROR] Role ID points to nothing!")
                 continue
            
            print(f"  Role: {role.name} (ID: {role.id}) | Role Company: {role.company_id}")
            
            if role.company_id != u.company_id:
                print(f"  [WARNING] Role Company ({role.company_id}) != User Company ({u.company_id})")

            # Check Permissions via Service Query Logic
            # select(Permission).join(RolePermission).where(...)
            stmt_perms = (
                select(Permission)
                .join(RolePermission, RolePermission.permission_id == Permission.id)
                .where(RolePermission.role_id == u.role_id)
                .where(Permission.company_id == u.company_id) # The logic used in service
            )
            perms = (await session.execute(stmt_perms)).scalars().all()
            print(f"  Permissions found via Service Logic: {len(perms)}")
            for p in perms:
                if "roles" in p.code or "users" in p.code:
                    print(f"    - {p.code}")
            if len(perms) == 0:
                print("  [CRITICAL] No permissions found! Checking why...")
                # Debug why
                # 1. Check raw RolePermissions
                raw_rp_stmt = select(RolePermission).where(RolePermission.role_id == u.role_id)
                raw_rps = (await session.execute(raw_rp_stmt)).scalars().all()
                print(f"    Raw RolePermissions entries: {len(raw_rps)}")
                
                if len(raw_rps) > 0:
                    first_rp = raw_rps[0]
                    perm_stmt = select(Permission).where(Permission.id == first_rp.permission_id)
                    perm = (await session.execute(perm_stmt)).scalar_one_or_none()
                    if perm:
                        print(f"    Sample Permission Company: {perm.company_id} vs User Company: {u.company_id}")

if __name__ == "__main__":
    asyncio.run(deep_inspect())
