
import asyncio
from app.database import async_session
from app.utils.role_seeder import seed_default_roles
from app.models import Company
from sqlalchemy import select

async def fix_roles_now():
    async with async_session() as session:
        # Get all companies
        stmt = select(Company)
        companies = (await session.execute(stmt)).scalars().all()
        
        print(f"Found {len(companies)} companies. Running role seeder for each...")
        
        for company in companies:
            print(f"Processing Company: {company.name} (ID: {company.id})")
            await seed_default_roles(session, company.id)
            print("  Done.")
            
        print("All companies updated.")

if __name__ == "__main__":
    asyncio.run(fix_roles_now())
