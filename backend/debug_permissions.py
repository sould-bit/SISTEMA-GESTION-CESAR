
import asyncio
from sqlalchemy import select
from app.database import async_session_factory
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission, RolePermission

async def inspect_permissions():
    async with async_session_factory() as session:
        # 1. Check all permissions in DB
        print("\n--- ALL PERMISSIONS IN DB ---")
        result = await session.execute(select(Permission))
        perms = result.scalars().all()
        for p in perms:
            print(f"Code: {p.code}, Name: {p.name}")

        # 2. Check Kate's Role and Permissions
        print("\n--- KATE TORI USER CHECK ---")
        result = await session.execute(select(User).where(User.email == "kate@gmail.com"))
        user = result.scalar_one_or_none()
        
        if user:
            print(f"User: {user.username}, Role ID: {user.role_id}")
            if user.role_id:
                # Get Role
                result = await session.execute(select(Role).where(Role.id == user.role_id))
                role = result.scalar_one_or_none()
                if role:
                    print(f"Role Code: {role.code}, Name: {role.name}")
                    
                    # Get Role Permissions
                    result = await session.execute(
                        select(Permission)
                        .join(RolePermission, RolePermission.permission_id == Permission.id)
                        .where(RolePermission.role_id == role.id)
                    )
                    role_perms = result.scalars().all()
                    print(f"Permissions for {role.name}:")
                    for rp in role_perms:
                        print(f" - {rp.code}")
                else:
                    print("Role not found in DB")
            else:
                print("User has no role_id")
        else:
            print("User kate@gmail.com not found")

if __name__ == "__main__":
    asyncio.run(inspect_permissions())
