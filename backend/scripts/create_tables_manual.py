import asyncio
import sys
from pathlib import Path

# Add backend directory to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import SQLModel
from app.database import engine
from app.models import Table
from app.models import * # Import all models to ensure metadata is populated

from app.config import settings

async def create_tables():
    print(f"DEBUG: DATABASE_URL loaded: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'INVALID'}")
    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    print("Tables created successfully!")

if __name__ == "__main__":
    asyncio.run(create_tables())
