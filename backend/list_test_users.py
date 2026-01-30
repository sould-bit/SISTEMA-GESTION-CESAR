import asyncio
from sqlalchemy import select
from app.database import async_session
from app.models import User, Role

async def list_data():
    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        print(f"\n{'USER ID':<5} | {'USERNAME':<15} | {'EMAIL':<25} | {'ROLE':<15}")
        print("-" * 70)
        
        for u in users:
            role_name = "No Role"
            if u.role_id:
                role = (await session.execute(select(Role).where(Role.id == u.role_id))).scalar_one_or_none()
                if role:
                    role_name = role.name
            
            print(f"{u.id:<5} | {u.username:<15} | {u.email:<25} | {role_name:<15}")

if __name__ == "__main__":
    asyncio.run(list_data())
