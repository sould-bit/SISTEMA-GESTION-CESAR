
import asyncio
from sqlalchemy import select
from app.database import async_session
from app.models import Permission, Role, RolePermission, User

async def inspect():
    async with async_session() as session:
        print("\n=== PERMISSIONS DUMP ===")
        result = await session.execute(select(Permission))
        perms = result.scalars().all()
        for p in perms:
            print(f"Company {p.company_id}: {p.code}")
            
        print("\n=== ADMIN USERS & ROLES ===")
        # Get all admin roles
        result = await session.execute(select(User).where(User.username == "mcesar.lalo")) # Owner
        user = result.scalar_one_or_none()
        if user:
             print(f"User: {user.username} (ID: {user.id}) RoleID: {user.role_id}")
             # Get his role
             if user.role_id:
                 role_res = await session.execute(select(Role).where(Role.id == user.role_id))
                 role = role_res.scalar_one_or_none()
                 if role:
                      print(f"  Role: {role.name} ({role.code})")
                      # Get Perms
                      stmt = select(Permission).join(RolePermission).where(RolePermission.role_id == role.id)
                      role_perms = (await session.execute(stmt)).scalars().all()
                      print(f"  Assigned Permissions ({len(role_perms)}):")
                      for rp in role_perms:
                          print(f"    - {rp.code}")

if __name__ == "__main__":
    asyncio.run(inspect())
