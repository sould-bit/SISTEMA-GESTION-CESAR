
import asyncio
from sqlalchemy import select
from app.database import async_session
from app.models import Permission

async def check_active():
    async with async_session() as session:
        result = await session.execute(select(Permission))
        perms = result.scalars().all()
        print(f"Total Perms: {len(perms)}")
        inactive = [p for p in perms if not p.is_active]
        print(f"Inactive Perms: {len(inactive)}")
        for p in inactive:
             print(f"Inactive: {p.code}")

if __name__ == "__main__":
    asyncio.run(check_active())
