
import asyncio
from sqlalchemy import select
from app.database import async_session
from app.models import User, Role

async def fix_legacy_users():
    async with async_session() as session:
        print("\n=== FINDING LEGACY USERS (role_id IS NULL) ===")
        stmt = select(User).where(User.role_id == None)
        result = await session.execute(stmt)
        users = result.scalars().all()
        
        print(f"Found {len(users)} users without role_id.")
        
        count = 0
        for user in users:
            print(f"Migrating User: {user.username} (Company {user.company_id}, Role string: {user.role})")
            
            # Find matching role
            stmt_role = select(Role).where(
                Role.company_id == user.company_id,
                Role.code == user.role
            )
            role = (await session.execute(stmt_role)).scalar_one_or_none()
            
            if role:
                print(f"  -> Found matching role ID: {role.id}")
                user.role_id = role.id
                session.add(user)
                count += 1
            else:
                print(f"  [!] NO MATCHING ROLE FOUND for code '{user.role}' in company {user.company_id}")
                # Fallback: Assign 'admin' role if username is admin?
                if user.role == "admin" or user.username == "admin":
                   print("  -> Trying to find 'admin' role...")
                   stmt_admin = select(Role).where(Role.company_id == user.company_id, Role.code == 'admin')
                   admin_role = (await session.execute(stmt_admin)).scalar_one_or_none()
                   if admin_role:
                       user.role_id = admin_role.id
                       session.add(user)
                       count += 1
        
        await session.commit()
        print(f"\nMigration complete. Updated {count} users.")

if __name__ == "__main__":
    asyncio.run(fix_legacy_users())
