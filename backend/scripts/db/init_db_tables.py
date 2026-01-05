import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

# Añadir path
sys.path.append(os.getcwd())

from app.config import settings
# Importar todos los modelos para que SQLModel los reconozca
from app.models import * 

async def create_tables():
    print("🔄 Creando tablas en base de datos...")
    engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        echo=True
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    print("✅ Tablas creadas (si no existían).")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables())
