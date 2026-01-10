"""Clean up orphaned inventory permissions."""
import asyncio
from sqlmodel import select
from app.database import async_session_maker
from app.models.permission import Permission

async def cleanup():
    async with async_session_maker() as db:
        result = await db.execute(
            select(Permission).where(Permission.code.like("inventory.%"))
        )
        perms = result.scalars().all()
        for p in perms:
            await db.delete(p)
            print(f"Deleted: {p.code}")
        await db.commit()
        print("Cleanup complete")

if __name__ == "__main__":
    asyncio.run(cleanup())
