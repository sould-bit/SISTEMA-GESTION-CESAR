import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from sqlmodel import SQLModel

sys.path.append(os.getcwd())
from app.config import settings
from app.models.print_queue import PrintJob

async def recreate_table():
    print("🔄 Recreando tabla print_jobs...")
    engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        echo=True
    )
    
    async with engine.begin() as conn:
        print("💥 Borrando tabla print_jobs...")
        await conn.execute(text("DROP TABLE IF EXISTS print_jobs CASCADE;"))
        
        print("🔨 Creando tabla print_jobs...")
        # create_all crea todas, pero solo las que faltan. 
        # Como acabamos de borrar print_jobs, la creará.
        await conn.run_sync(SQLModel.metadata.create_all)
    
    print("✅ Tabla recreada.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(recreate_table())
